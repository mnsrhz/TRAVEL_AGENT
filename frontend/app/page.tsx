"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { API_BASE_URL, approveGate, createSession, exportUrl, sendMessage } from "../lib/api";
import type { ChatMessage, ItineraryDay, ItineraryEvent, SessionResponse, TraceEvent, TravelState, WorkflowState } from "../lib/types";

const WORKFLOW = [
  "Collect preferences",
  "Research options",
  "Approve destination split",
  "Build itinerary",
  "Review & critique",
  "Approve itinerary",
  "Generate calendar",
  "Export ICS file"
];

const QUICK_REPLIES = ["Japan", "Italy", "Mexico", "Thailand", "A quiet food-focused trip"];

const TOOL_ROWS = [
  { key: "tavily", icon: "ti-world-search", name: "Tavily search", match: ["Tavily"] },
  { key: "flights", icon: "ti-plane-departure", name: "SerpAPI flights", match: ["Flights", "flight"] },
  { key: "hotels", icon: "ti-building", name: "SerpAPI hotels", match: ["Hotels", "hotel"] },
  { key: "places", icon: "ti-map-pin", name: "Google Places", match: ["Places", "Restaurant", "restaurant"] },
  { key: "maps", icon: "ti-route", name: "Google Maps", match: ["Maps", "Transit", "transit"] }
];

function emptyState(): TravelState {
  return {
    user_input: {},
    preferences: {},
    destination_plan: {},
    flights: [],
    hotels: [],
    attractions: [],
    restaurants: [],
    transit_estimates: [],
    itinerary: [],
    review: {},
    approvals: {},
    current_state: "COLLECTING_REQUIREMENTS",
    tool_call_count: 0,
    token_count: 0,
    review_iteration_count: 0,
    planner_iteration_count: 0,
    trace_events: [],
    errors: [],
    generated_ics: null
  };
}

export default function Home() {
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [message, setMessage] = useState("");
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [filter, setFilter] = useState<"all" | "plan" | "tool" | "critique">("all");

  useEffect(() => {
    let cancelled = false;
    createSession()
      .then((payload) => {
        if (!cancelled) setSession(payload);
      })
      .catch((err: Error) => setError(err.message));
    return () => {
      cancelled = true;
    };
  }, []);

  const state = session?.state || emptyState();
  const activeStep = stepForState(state.current_state);
  const prefs = Object.keys(state.preferences).length ? state.preferences : state.user_input;
  const title = titleForState(state);
  const trace = state.trace_events || [];
  const filteredTrace = trace.filter((event) => filter === "all" || traceKind(event) === filter);

  async function submitChat(event?: FormEvent, preset?: string) {
    event?.preventDefault();
    const text = (preset || message).trim();
    if (!text || !session || working) return;
    setMessage("");
    setError(null);
    setWorking(true);
    const optimistic: SessionResponse = {
      ...session,
      chat_history: [...session.chat_history, { role: "user", content: text }]
    };
    setSession(optimistic);
    try {
      const payload = await sendMessage(session.session_id, text);
      setSession(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to send message");
      setSession(session);
    } finally {
      setWorking(false);
    }
  }

  async function approve(gate: string) {
    if (!session || working) return;
    setError(null);
    setWorking(true);
    try {
      const payload = await approveGate(session.session_id, gate);
      setSession(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to approve gate");
    } finally {
      setWorking(false);
    }
  }

  async function resetTrip() {
    setWorking(true);
    setError(null);
    try {
      setSession(await createSession());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start a new trip");
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-icon">
            <i className="ti ti-plane" />
          </div>
          <div>
            <div className="logo-text">Travel Concierge</div>
            <div className="logo-sub">Agentic AI system</div>
          </div>
        </div>

        <div>
          <div className="sec-label">Workflow</div>
          <div className="step-list">
            {WORKFLOW.map((name, index) => (
              <div key={name} className={`step ${index === activeStep ? "active" : ""} ${index > activeStep ? "pending" : ""}`}>
                <div className={`step-dot ${dotState(index, activeStep, working, state.current_state)}`}>
                  {index < activeStep ? <i className="ti ti-check" /> : index + 1}
                </div>
                <span className="step-name">{name}</span>
              </div>
            ))}
          </div>
        </div>

        {Object.keys(prefs).length > 0 && (
          <div>
            <div className="sec-label">Collected so far</div>
            <div className="prefs-collected">
              <PrefChip icon="ti-map-2" label="Destination" value={stringValue(prefs.destination)} />
              <PrefChip icon="ti-plane-departure" label="Departure" value={stringValue(prefs.origin)} />
              <PrefChip icon="ti-calendar" label="Dates" value={formatDateRange(prefs)} />
              <PrefChip icon="ti-wallet" label="Budget" value={moneyValue(prefs.budget)} />
              <PrefChip icon="ti-salad" label="Dietary" value={stringValue(prefs.dietary)} />
              <PrefChip icon="ti-run" label="Pace" value={stringValue(prefs.pace)} />
            </div>
          </div>
        )}

        <div>
          <div className="sec-label">Tool activity</div>
          <div className="tool-list">
            {TOOL_ROWS.map((tool) => {
              const status = toolStatus(tool.match, state, working);
              return (
                <div className="tool-row" key={tool.key}>
                  <i className={`ti ${tool.icon}`} />
                  <span className="tool-name">{tool.name}</span>
                  <span className={status.className}>{status.label}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="token-block">
          <div className="sec-label">Token usage</div>
          <div className="token-bar-bg">
            <div className="token-bar-fill" style={{ width: `${Math.min(100, Math.max(2, state.token_count / 1000))}%` }} />
          </div>
          <div className="token-nums">
            <span>{numberValue(state.token_count)} used</span>
            <span>100k max</span>
          </div>
        </div>
      </aside>

      <main className="main">
        <div className="topbar">
          <span className="topbar-title">{title}</span>
          <div className="topbar-meta">
            <span className="badge badge-info">{modeLabel()}</span>
            <span className={state.errors.length ? "badge badge-warn" : "badge badge-success"}>
              {state.errors.length ? `${state.errors.length} issue${state.errors.length > 1 ? "s" : ""}` : "Ready"}
            </span>
          </div>
        </div>

        <section className={`screen ${activeStep === 0 ? "active" : ""}`}>
          <div className="chat-onboard">
            <div className="chat-messages">
              {(session?.chat_history || [{ role: "assistant", content: "Hi! I'm your AI travel concierge. Where in the world are you dreaming of going?" } as ChatMessage]).map(
                (chat, index) =>
                  chat.role === "assistant" ? (
                    <div className="msg-agent" key={`${chat.role}-${index}`}>
                      <div className="agent-avatar">
                        <i className="ti ti-plane" />
                      </div>
                      <div className="msg-bubble-agent">{chat.content}</div>
                    </div>
                  ) : (
                    <div className="msg-user" key={`${chat.role}-${index}`}>
                      <div className="msg-bubble-user">{chat.content}</div>
                    </div>
                  )
              )}
              {working && activeStep === 0 && <TypingIndicator />}
            </div>
            {state.current_state === "COLLECTING_REQUIREMENTS" && (
              <div className="quick-replies">
                {QUICK_REPLIES.map((reply) => (
                  <button className="qr-chip" key={reply} onClick={() => submitChat(undefined, reply)} disabled={working}>
                    {reply}
                  </button>
                ))}
              </div>
            )}
            {state.current_state === "AWAITING_PREFERENCE_APPROVAL" && (
              <div className="summary-card">
                <div className="summary-card-title">Preference confirmation</div>
                <SummaryGrid prefs={prefs} />
                <div className="approval-choices approval-inline">
                  <button className="btn btn-primary btn-lg" onClick={() => approve("preference_confirmation")} disabled={working}>
                    <i className="ti ti-check" /> Approve preferences and research
                  </button>
                  <button className="btn" onClick={resetTrip} disabled={working}>
                    <i className="ti ti-edit" /> Start over
                  </button>
                </div>
              </div>
            )}
            <form className="onboard-bar" onSubmit={submitChat}>
              <input
                className="onboard-input"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="Type your answer..."
                disabled={working || state.current_state !== "COLLECTING_REQUIREMENTS"}
              />
              <button className="onboard-send" type="submit" disabled={working || !message.trim()}>
                <i className="ti ti-arrow-up" />
              </button>
            </form>
          </div>
        </section>

        <section className={`screen ${activeStep === 1 ? "active" : ""}`}>
          <div className="content">
            <div className="section-heading">Researching your trip</div>
            <div className="progress-wrap">
              {TOOL_ROWS.map((tool, index) => {
                const status = toolStatus(tool.match, state, working);
                return (
                  <div className={`progress-item ${status.progress}`} key={tool.key}>
                    {status.progress === "done" ? (
                      <div className="progress-check">
                        <i className="ti ti-check" />
                      </div>
                    ) : status.progress === "running" ? (
                      <div className="progress-spinner" />
                    ) : (
                      <div className="progress-pending-dot" />
                    )}
                    <div>
                      <div className="progress-label">{researchLabel(index)}</div>
                      <div className="progress-sub">{tool.name}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <section className={`screen ${activeStep === 2 ? "active" : ""}`}>
          <div className="content">
            <div className="section-heading">Research complete</div>
            <div className="pref-grid">
              <Metric label="Flights found" icon="ti-plane-departure" value={`${state.flights.length || 0} options`} />
              <Metric label="Hotels found" icon="ti-building" value={`${state.hotels.length || 0} properties`} />
              <Metric label="Attractions" icon="ti-map-pin" value={`${state.attractions.length || 0} curated`} />
              <Metric label="Restaurants" icon="ti-salad" value={`${state.restaurants.length || 0} matched`} />
            </div>
            <ApprovalPanel
              title="Approval gate 2 of 5 - Destination allocation"
              body={destinationBody(state)}
              primaryLabel="Approve split"
              primaryIcon="ti-check"
              onPrimary={() => approve("destination_city_split")}
              disabled={working}
            />
          </div>
        </section>

        <section className={`screen ${activeStep === 3 ? "active" : ""}`}>
          <div className="content">
            <div className="section-heading">Draft itinerary</div>
            <Itinerary itinerary={state.itinerary} prefs={prefs} />
          </div>
        </section>

        <section className={`screen ${activeStep === 4 || activeStep === 5 ? "active" : ""}`}>
          <div className="content">
            <div className="section-heading">Review agent output</div>
            <ReviewBlock state={state} />
            {state.current_state === "AWAITING_HIGH_RISK_DAY_APPROVAL" && (
              <ApprovalPanel
                title="Approval gate 3 of 5 - Safety review"
                body="The review agent found items that need explicit approval before the itinerary can be finalized."
                primaryLabel="Approve safety review"
                primaryIcon="ti-shield-check"
                onPrimary={() => approve("high_risk_day")}
                disabled={working}
              />
            )}
            {state.current_state === "AWAITING_ITINERARY_APPROVAL" && (
              <ApprovalPanel
                title="Approval gate 4 of 5 - Itinerary review"
                body="Approve the reviewed itinerary or start over with revised preferences."
                primaryLabel="Approve itinerary"
                primaryIcon="ti-check"
                onPrimary={() => approve("final_itinerary")}
                disabled={working}
              />
            )}
          </div>
        </section>

        <section className={`screen ${activeStep === 6 ? "active" : ""}`}>
          <div className="content">
            <div className="section-heading">Calendar preview</div>
            <CalendarPreview itinerary={state.itinerary} />
            <ApprovalPanel
              title="Approval gate 5 of 5 - Calendar generation"
              body={`The agent will generate ${eventCount(state.itinerary)} calendar events covering travel, lodging, attractions, meals, and transit.`}
              primaryLabel="Generate calendar"
              primaryIcon="ti-calendar-plus"
              onPrimary={() => approve("calendar_creation")}
              disabled={working}
            />
          </div>
        </section>

        <section className={`screen ${activeStep === 7 ? "active" : ""}`}>
          <div className="content">
            <div className="export-success">
              <div className="success-icon">
                <i className="ti ti-circle-check" />
              </div>
              <div className="success-title">Your trip is ready</div>
              <div className="success-sub">
                The agent generated a complete itinerary with calendar-ready events. Download the ICS file to import into
                Google Calendar, Apple Calendar, or Outlook.
              </div>
              <div className="stat-row">
                <Stat value={eventCount(state.itinerary)} label="Calendar events" />
                <Stat value={state.itinerary.length} label="Days planned" />
                <Stat value={moneyValue(prefs.budget) || "Flexible"} label="Budget" />
                <Stat value={state.restaurants.length || 0} label="Restaurants" />
              </div>
              {session && (
                <div className="download-row">
                  <a className="download-btn" href={exportUrl(session.session_id, "calendar.ics")}>
                    <i className="ti ti-download" /> Download ICS file
                  </a>
                  <a className="btn btn-lg" href={exportUrl(session.session_id, "itinerary.md")}>
                    <i className="ti ti-file-text" /> Itinerary markdown
                  </a>
                </div>
              )}
              <button className="btn" onClick={resetTrip}>
                <i className="ti ti-plus" /> Plan another trip
              </button>
            </div>
          </div>
        </section>

        {activeStep > 0 && (
          <form className="bottombar" onSubmit={submitChat}>
            <input
              className="chat-input"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Start a new request in plain English..."
              disabled={working}
            />
            <button className="send-btn" type="submit" disabled={working || !message.trim()}>
              <i className="ti ti-arrow-up" />
            </button>
          </form>
        )}
        {error && <div className="toast show">{error}</div>}
      </main>

      <aside className={`reasoning-wrapper ${collapsed ? "collapsed" : ""}`}>
        <div className="collapse-rail" onClick={() => setCollapsed(!collapsed)}>
          <button className="collapse-btn" aria-label="Toggle reasoning panel">
            <i className="ti ti-chevron-right" />
          </button>
          <span className="rail-label">Agent reasoning</span>
        </div>
        <div className="reasoning">
          <div className="reasoning-topbar">
            <div className="reasoning-topbar-title">
              <i className="ti ti-brain" /> Agent reasoning
            </div>
            <div className="reasoning-filter">
              {(["all", "plan", "tool", "critique"] as const).map((item) => (
                <button className={`filter-pill ${filter === item ? "active" : ""}`} onClick={() => setFilter(item)} key={item}>
                  {item[0].toUpperCase() + item.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <div className="reasoning-body">
            {filteredTrace.length === 0 ? (
              <div className="reasoning-placeholder">Reasoning traces will appear as the agent works.</div>
            ) : (
              filteredTrace.map((event) => <ThoughtCard event={event} key={`${event.step}-${event.node}-${event.action}`} />)
            )}
          </div>
        </div>
      </aside>
      {working && activeStep !== 0 && (
        <div className="working-overlay">
          <TypingIndicator />
          <span>Agent is working</span>
        </div>
      )}
    </div>
  );
}

function PrefChip({ icon, label, value }: { icon: string; label: string; value?: string }) {
  if (!value) return null;
  return (
    <div className="pref-chip">
      <i className={`ti ${icon}`} />
      <div className="pref-chip-text">
        <span className="pref-chip-label">{label}</span>
        {value}
      </div>
    </div>
  );
}

function SummaryGrid({ prefs }: { prefs: Record<string, unknown> }) {
  return (
    <div className="summary-grid">
      <SummaryItem label="Destination" value={stringValue(prefs.destination)} />
      <SummaryItem label="Departure" value={stringValue(prefs.origin)} />
      <SummaryItem label="Dates" value={formatDateRange(prefs)} />
      <SummaryItem label="Budget" value={moneyValue(prefs.budget)} />
      <SummaryItem label="Dietary" value={stringValue(prefs.dietary)} full />
      <SummaryItem label="Pace" value={stringValue(prefs.pace)} full />
    </div>
  );
}

function SummaryItem({ label, value, full }: { label: string; value?: string; full?: boolean }) {
  return (
    <div className={`summary-item ${full ? "full" : ""}`}>
      <span className="summary-label">{label}</span>
      <span className="summary-value">{value || "Pending"}</span>
    </div>
  );
}

function Metric({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="pref-card">
      <div className="pref-label">{label}</div>
      <div className="pref-val">
        <i className={`ti ${icon}`} />
        {value}
      </div>
    </div>
  );
}

function ApprovalPanel({
  title,
  body,
  primaryLabel,
  primaryIcon,
  onPrimary,
  disabled
}: {
  title: string;
  body: string;
  primaryLabel: string;
  primaryIcon: string;
  onPrimary: () => void;
  disabled: boolean;
}) {
  return (
    <div className="approval-panel">
      <div className="approval-header">
        <i className="ti ti-alert-triangle" />
        <span className="approval-header-text">{title}</span>
      </div>
      <div className="approval-body">
        <p>{body}</p>
        <div className="approval-choices">
          <button className="btn btn-primary" onClick={onPrimary} disabled={disabled}>
            <i className={`ti ${primaryIcon}`} /> {primaryLabel}
          </button>
          <button className="btn" disabled={disabled}>
            <i className="ti ti-edit" /> Request changes
          </button>
        </div>
      </div>
    </div>
  );
}

function Itinerary({ itinerary, prefs }: { itinerary: ItineraryDay[]; prefs: Record<string, unknown> }) {
  if (!itinerary.length) {
    return <div className="empty-card">The itinerary will appear here as soon as the agent builds it.</div>;
  }
  return (
    <div className="itinerary">
      <div className="itin-header">
        <span className="itin-header-left">Day-by-day schedule</span>
        <span className="itin-header-right">
          {stringValue(prefs.destination) || "Destination"} - {itinerary.length} days
        </span>
      </div>
      {itinerary.map((day) => (
        <div key={`${day.day}-${day.date}`}>
          <div className="day-label">
            Day {day.day} - {formatShortDate(day.date)} - {day.city}
          </div>
          {day.events.map((event, index) => (
            <EventRow event={event} key={`${event.start}-${index}`} />
          ))}
        </div>
      ))}
    </div>
  );
}

function EventRow({ event }: { event: ItineraryEvent }) {
  return (
    <div className="event-row">
      <span className="event-time">{formatTime(event.start)}</span>
      <div className={`event-dot ${dotForEvent(event.type)}`} />
      <div>
        <div className="event-title">{event.title}</div>
        <div className="event-sub">
          {event.location}
          {event.cost ? ` - ${event.cost}` : ""}
        </div>
        <span className={`event-tag ${tagForEvent(event.type)}`}>{event.type}</span>
      </div>
    </div>
  );
}

function ReviewBlock({ state }: { state: TravelState }) {
  const score = numberFromUnknown(state.review.score, 8);
  const warnings = arrayFromUnknown(state.review.warnings);
  const passes = arrayFromUnknown(state.review.passes);
  return (
    <div className="critique-block">
      <div className="critique-header">Quality assessment - draft itinerary</div>
      <div className="critique-body">
        <ScoreRow label="Overall quality" score={score} />
        <ScoreRow label="Budget adherence" score={Math.min(10, score + 0.5)} />
        <ScoreRow label="Dietary compliance" score={10} />
        <ScoreRow label="Schedule realism" score={Math.max(6, score - 1)} />
        <div className="thought-divider" />
        {(warnings.length ? warnings : ["No blocking review issues found."]).map((warning) => (
          <div className="flag-row" key={warning}>
            <i className="ti ti-alert-circle" />
            <span className="flag-text">{warning}</span>
          </div>
        ))}
        {(passes.length ? passes : ["Calendar-ready structure confirmed."]).map((pass) => (
          <div className="pass-row" key={pass}>
            <i className="ti ti-check" />
            <span className="pass-text">{pass}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ScoreRow({ label, score }: { label: string; score: number }) {
  return (
    <div className="score-row">
      <span className="score-label">{label}</span>
      <div className="score-bar-bg">
        <div className="score-bar-fill" style={{ width: `${Math.max(0, Math.min(100, score * 10))}%` }} />
      </div>
      <span className="score-num">{score}/10</span>
    </div>
  );
}

function CalendarPreview({ itinerary }: { itinerary: ItineraryDay[] }) {
  const days = itinerary.slice(0, 5);
  if (!days.length) return <div className="empty-card">Calendar preview will appear after itinerary approval.</div>;
  return (
    <div className="cal-grid">
      {days.map((day) => (
        <div className="cal-day" key={`${day.day}-${day.date}`}>
          <div className="cal-day-label">
            {formatShortDate(day.date)} (Day {day.day})
          </div>
          {day.events.slice(0, 4).map((event) => (
            <div className={`cal-event ${calendarClass(event.type)}`} key={`${event.start}-${event.title}`}>
              {formatTime(event.start)} {event.title}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function ThoughtCard({ event }: { event: TraceEvent }) {
  const kind = traceKind(event);
  return (
    <div className="thought-card">
      <div className="thought-header">
        <div className={`thought-icon icon-${kind}`}>
          <i className={`ti ${iconForKind(kind)}`} />
        </div>
        <div className="thought-meta">
          <div className="thought-title">{event.node}</div>
          <div className="thought-time">{formatTraceTime(event.timestamp)}</div>
        </div>
        <span className={`thought-type type-${kind}`}>{kind}</span>
      </div>
      <div className="thought-body">
        <div className="thought-text">{event.input_summary}</div>
        <div className="thought-reasoning">{event.output_summary}</div>
        {event.decision && (
          <>
            <div className="thought-divider" />
            <div className="kv-row">
              <span className="kv-label">Decision</span>
              <span className="kv-val">{event.decision}</span>
            </div>
          </>
        )}
        {event.error && (
          <div className="flag-row">
            <i className="ti ti-alert-circle" />
            <span className="flag-text">{event.error}</span>
          </div>
        )}
      </div>
      <div className="thought-footer">
        <span className="token-chip">
          <i className="ti ti-coins" /> {event.tokens_used || 0} tokens
        </span>
        <span className="token-chip">
          <i className="ti ti-tool" /> {event.tool_calls_used || 0} tools
        </span>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <div className="agent-avatar">
        <i className="ti ti-plane" />
      </div>
      <div className="typing-dots">
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}

function Stat({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="stat-chip">
      <div className="stat-num">{value}</div>
      <div className="stat-lbl">{label}</div>
    </div>
  );
}

function stepForState(state: WorkflowState): number {
  const map: Record<WorkflowState, number> = {
    COLLECTING_REQUIREMENTS: 0,
    AWAITING_PREFERENCE_APPROVAL: 0,
    RESEARCHING: 1,
    AWAITING_DESTINATION_APPROVAL: 2,
    BUILDING_ITINERARY: 3,
    REVIEWING: 4,
    AWAITING_HIGH_RISK_DAY_APPROVAL: 4,
    AWAITING_ITINERARY_APPROVAL: 5,
    AWAITING_CALENDAR_APPROVAL: 6,
    GENERATING_CALENDAR: 6,
    COMPLETE: 7,
    FAILED: 0
  };
  return map[state];
}

function dotState(index: number, activeStep: number, working: boolean, state: WorkflowState) {
  if (index < activeStep) return "done";
  if (index === activeStep && working) return "running";
  if (index === activeStep) return "active";
  if (state === "COMPLETE" && index === 7) return "done";
  return "pending";
}

function titleForState(state: TravelState) {
  if (state.current_state === "COLLECTING_REQUIREMENTS") return "Let's plan your trip";
  if (state.current_state === "AWAITING_PREFERENCE_APPROVAL") return "Confirm your preferences";
  if (state.current_state === "RESEARCHING") return "Researching live options";
  if (state.current_state === "AWAITING_DESTINATION_APPROVAL") return "Approve destination split";
  if (state.current_state === "AWAITING_CALENDAR_APPROVAL") return "Calendar preview";
  if (state.current_state === "COMPLETE") return "Your trip is ready";
  return `${stringValue(state.preferences.destination) || "Travel"} itinerary`;
}

function toolStatus(match: string[], state: TravelState, working: boolean) {
  const event = [...state.trace_events].reverse().find((item) => match.some((token) => `${item.node} ${item.action}`.includes(token)));
  if (event) {
    return {
      label: event.status === "fallback" ? "Fallback" : event.status === "error" ? "Issue" : "Done",
      className: event.status === "error" ? "t-warn" : "t-done",
      progress: "done"
    };
  }
  if (working || state.current_state === "RESEARCHING") return { label: "Running", className: "t-run", progress: "running" };
  return { label: "Waiting", className: "t-wait", progress: "pending" };
}

function traceKind(event: TraceEvent): "plan" | "tool" | "critique" | "decision" {
  const text = `${event.node} ${event.event_type} ${event.action}`.toLowerCase();
  if (text.includes("tool") || text.includes("search") || text.includes("flight") || text.includes("hotel") || text.includes("maps")) return "tool";
  if (text.includes("review") || text.includes("critique")) return "critique";
  if (text.includes("approval") || text.includes("decision")) return "decision";
  return "plan";
}

function iconForKind(kind: string) {
  if (kind === "tool") return "ti-tool";
  if (kind === "critique") return "ti-scale";
  if (kind === "decision") return "ti-check";
  return "ti-route";
}

function researchLabel(index: number) {
  return [
    "Searching destinations and attractions",
    "Looking up flight options",
    "Finding hotels",
    "Sourcing restaurants",
    "Calculating travel distances"
  ][index];
}

function destinationBody(state: TravelState) {
  const cities = Array.isArray(state.destination_plan.cities) ? state.destination_plan.cities : [];
  if (cities.length) {
    const split = cities
      .map((city) => {
        const item = city as Record<string, unknown>;
        return `${stringValue(item.city)} ${stringValue(item.days)} days`;
      })
      .join(" - ");
    return `Based on your preferences and travel distances, the agent proposes this destination allocation: ${split}. Approve to begin itinerary generation.`;
  }
  return "Approve the researched destination plan before the itinerary agent builds a day-by-day schedule.";
}

function formatDateRange(prefs: Record<string, unknown>) {
  const start = stringValue(prefs.start_date);
  const days = numberFromUnknown(prefs.days, 0);
  if (!start && !days) return undefined;
  return `${start || "Flexible"}${days ? ` - ${days} days` : ""}`;
}

function stringValue(value: unknown) {
  if (value === null || value === undefined || value === "") return undefined;
  return String(value);
}

function moneyValue(value: unknown) {
  const num = numberFromUnknown(value, 0);
  if (!num) return stringValue(value);
  return `$${num.toLocaleString()}`;
}

function numberValue(value: number) {
  return value.toLocaleString();
}

function numberFromUnknown(value: unknown, fallback: number) {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
}

function arrayFromUnknown(value: unknown) {
  return Array.isArray(value) ? value.map(String) : [];
}

function formatShortDate(value: string) {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function formatTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--:--";
  return date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

function formatTraceTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

function dotForEvent(type: string) {
  if (type.includes("flight") || type.includes("train")) return "dot-blue";
  if (type.includes("meal") || type.includes("food")) return "dot-amber";
  if (type.includes("hotel")) return "dot-purple";
  return "dot-teal";
}

function tagForEvent(type: string) {
  if (type.includes("flight") || type.includes("train")) return "tag-flight";
  if (type.includes("meal") || type.includes("food")) return "tag-food";
  if (type.includes("hotel")) return "tag-hotel";
  return "tag-attraction";
}

function calendarClass(type: string) {
  if (type.includes("flight") || type.includes("train")) return "cal-flight";
  if (type.includes("meal") || type.includes("food")) return "cal-food";
  if (type.includes("hotel")) return "cal-hotel";
  return "cal-attract";
}

function eventCount(itinerary: ItineraryDay[]) {
  return itinerary.reduce((total, day) => total + day.events.length, 0);
}

function modeLabel() {
  return "Live API workflow";
}
