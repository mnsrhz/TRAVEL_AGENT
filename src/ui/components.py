from __future__ import annotations

from datetime import datetime, timedelta
import html

import streamlit as st

from src.config.settings import Settings
from src.state.travel_state import TravelState, WorkflowState


WORKFLOW_STEPS = [
    ("Collect preferences", WorkflowState.COLLECTING_REQUIREMENTS),
    ("Research options", WorkflowState.RESEARCHING),
    ("Build itinerary", WorkflowState.BUILDING_ITINERARY),
    ("Review & critique", WorkflowState.REVIEWING),
    ("Approval gate", WorkflowState.AWAITING_PREFERENCE_APPROVAL),
    ("Generate calendar", WorkflowState.GENERATING_CALENDAR),
    ("Export ICS file", WorkflowState.COMPLETE),
]


def render_shell_marker() -> None:
    st.markdown('<div class="tc-app-shell" aria-hidden="true"></div>', unsafe_allow_html=True)


def render_workflow_sidebar(state: TravelState, settings: Settings) -> None:
    st.markdown(
        """
        <div class="tc-logo">
          <div class="tc-logo-icon">✈</div>
          <div>
            <div class="tc-logo-text">Travel Concierge</div>
            <div class="tc-logo-sub">Agentic AI system</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_environment(settings)
    st.markdown('<div class="tc-sec-label">Workflow</div><div class="tc-step-list">', unsafe_allow_html=True)
    active_index = _active_step_index(state)
    for index, (label, _) in enumerate(WORKFLOW_STEPS, start=1):
        status = "done" if index < active_index else "active" if index == active_index else "pending"
        dot = "✓" if status == "done" else str(index)
        st.markdown(
            f"""
            <div class="tc-step {status}">
              <div class="tc-step-dot {status}">{html.escape(dot)}</div>
              <span class="tc-step-name">{html.escape(label)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_environment(settings: Settings) -> None:
    badge = "tc-badge-green" if settings.allow_demo_fallbacks else "tc-badge-amber"
    st.markdown(f'<span class="tc-badge {badge}">{html.escape(settings.mode_label)}</span>', unsafe_allow_html=True)
    if settings.missing_keys:
        st.caption("Missing keys: " + ", ".join(settings.missing_keys))


def render_tool_readiness(settings: Settings) -> None:
    st.markdown('<div class="tc-sec-label">Tool activity</div>', unsafe_allow_html=True)
    tools = [
        ("◎", "Tavily search", "TAVILY_API_KEY"),
        ("✈", "SerpAPI flights", "SERPAPI_API_KEY"),
        ("▣", "SerpAPI hotels", "SERPAPI_API_KEY"),
        ("⌖", "Google Places", "GOOGLE_MAPS_API_KEY"),
        ("↝", "Google Maps", "GOOGLE_MAPS_API_KEY"),
    ]
    for icon, label, key in tools:
        status, status_class = _tool_status(settings, key)
        st.markdown(
            f"""
            <div class="tc-tool-row">
              <span class="tc-tool-icon">{html.escape(icon)}</span>
              <span class="tc-tool-name">{html.escape(label)}</span>
              <span class="{status_class}">{html.escape(status)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    usage = min(100, int((settings.allow_demo_fallbacks or 0) * 8))
    st.markdown(
        f"""
        <div class="tc-token-block">
          <div class="tc-sec-label">Token usage</div>
          <div class="tc-token-bar-bg"><div class="tc-token-bar-fill" style="width:{usage}%;"></div></div>
          <div class="tc-token-nums"><span>0 used</span><span>100k max</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topbar(state: TravelState, settings: Settings) -> None:
    trip = _active_trip(state)
    destination = str(trip.get("destination", "New trip"))
    days = trip.get("days", "Tell me your dates")
    title = f"{days}-day {destination}" if destination != "New trip" else "Travel Concierge"
    pace = str(trip.get("pace", "Chat intake")).title()
    budget = f"${trip.get('budget'):,}" if isinstance(trip.get("budget"), int) else "Budget pending"
    dietary = str(trip.get("dietary", "Dietary pending")).title()
    mode_class = "tc-badge-green" if settings.allow_demo_fallbacks else "tc-badge-amber"
    st.markdown(
        f"""
        <div class="tc-topbar">
          <span class="tc-topbar-title">{html.escape(title)}</span>
          <div class="tc-topbar-meta">
            <span class="tc-badge tc-badge-blue">{html.escape(pace)}</span>
            <span class="tc-badge tc-badge-green">{html.escape(budget)}</span>
            <span class="tc-badge tc-badge-amber">{html.escape(dietary)}</span>
            <span class="tc-badge {mode_class}">{html.escape(settings.mode_label)}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_main_content_start() -> None:
    st.markdown('<div class="tc-main-content">', unsafe_allow_html=True)


def render_main_content_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_preferences(state: TravelState) -> None:
    trip = _active_trip(state)
    items = [
        ("Departure", "✈", trip.get("origin")),
        ("Dates", "▦", _date_range_label(trip)),
        ("Pace", "↝", _title_text(trip.get("pace"))),
        ("Budget", "$", f"${trip.get('budget'):,}" if isinstance(trip.get("budget"), int) else None),
        ("Dietary", "♧", _title_text(trip.get("dietary"))),
        ("Destination", "⌖", trip.get("destination")),
    ]
    status = "Confirmed" if state.preferences else "Collecting"
    st.markdown(
        f"""
        <div>
          <div class="tc-section-title-row">
            <div class="tc-section-heading">Trip preferences</div>
            <span class="tc-mini-state">{html.escape(status)}</span>
          </div>
          <div class="tc-pref-grid">
        """,
        unsafe_allow_html=True,
    )
    rendered = 0
    for label, icon, value in items:
        if value in {None, ""}:
            continue
        rendered += 1
        st.markdown(
            f"""
            <div class="tc-pref-card">
              <div class="tc-pref-label">{html.escape(label)}</div>
              <div class="tc-pref-val"><span class="tc-pref-icon">{html.escape(icon)}</span>{html.escape(str(value))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if not rendered:
        st.markdown(
            '<div class="tc-pref-card tc-pref-card-empty"><div class="tc-pref-label">Waiting</div>'
            '<div class="tc-pref-val">Tell me about the trip you want</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_status(state: TravelState) -> None:
    if state.current_state != WorkflowState.FAILED:
        return
    errors = [event.error for event in state.trace_events if event.error]
    message = errors[-1] if errors else "The workflow stopped before completing."
    st.error(message)


def render_itinerary(state: TravelState) -> None:
    st.markdown(
        '<div><div class="tc-section-heading">Draft itinerary</div><div class="tc-itinerary">'
        '<div class="tc-itin-header"><span class="tc-itin-header-left">Day-by-day schedule</span>'
        f'<span class="tc-itin-header-right">{html.escape(_city_summary(state))}</span></div>',
        unsafe_allow_html=True,
    )
    for day in state.itinerary:
        st.markdown(
            f'<div class="tc-day-label">Day {html.escape(str(day.get("day", "?")))} — {html.escape(str(day.get("date", "Date TBD")))} · {html.escape(str(day.get("city", "")))}</div>',
            unsafe_allow_html=True,
        )
        for event in day.get("events", []):
            event_type = str(event.get("type", "event"))
            start = str(event.get("start", ""))
            start_label = start[11:16] if len(start) >= 16 else start
            st.markdown(
                f"""
                <div class="tc-event-row">
                  <span class="tc-event-time">{html.escape(start_label)}</span>
                  <div class="tc-event-dot {_dot_class(event_type)}"></div>
                  <div>
                    <div class="tc-event-title">{html.escape(str(event.get('title', 'Untitled event')))}</div>
                    <div class="tc-event-sub">{html.escape(str(event.get('location', event.get('description', ''))))}</div>
                    <span class="tc-event-tag {_tag_class(event_type)}">{html.escape(event_type.title())}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_destination_plan(state: TravelState) -> None:
    if not state.destination_plan:
        return
    st.markdown('<div><div class="tc-section-heading">Destination split</div><div class="tc-pref-grid">', unsafe_allow_html=True)
    for city in state.destination_plan.get("cities", []):
        st.markdown(
            f'<div class="tc-pref-card"><div class="tc-pref-label">{html.escape(str(city.get("nights", "")))} nights</div>'
            f'<div class="tc-pref-val">{html.escape(str(city.get("city", "")))}</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_review_summary(state: TravelState) -> None:
    if not state.review:
        return
    findings = state.review.get("findings", [])
    st.markdown(
        f"""
        <div class="tc-card">
          <div class="tc-pref-label">Review score</div>
          <div class="tc-pref-val">{html.escape(str(state.review.get("score", "n/a")))} / 10</div>
          <div class="tc-event-sub">{html.escape("; ".join(str(item) for item in findings))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_approval_panel(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="tc-approval">
          <div class="tc-approval-head">⚠ {html.escape(title)}</div>
          <div class="tc-approval-body">
            <p>{html.escape(body)}</p>
            <div class="tc-approval-actions">
              <span class="tc-faux-btn primary">✓ Approve</span>
              <span class="tc-faux-btn">✎ Modify</span>
              <span class="tc-faux-btn danger">↻ Regenerate</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bottom_chat_hint() -> None:
    st.markdown('<div class="tc-bottom-chat">Ask a question or give feedback below.</div>', unsafe_allow_html=True)


def render_trace_panel(state: TravelState) -> None:
    st.markdown(
        """
        <div class="tc-reasoning-wrapper">
          <div class="tc-reasoning-topbar">
            <div class="tc-reasoning-title">🧠 Agent reasoning</div>
            <div class="tc-reasoning-filter">
              <span class="tc-filter-pill active">All</span>
              <span class="tc-filter-pill">Plan</span>
              <span class="tc-filter-pill">Tool</span>
              <span class="tc-filter-pill">Critique</span>
            </div>
          </div>
          <div class="tc-reasoning-body">
        """,
        unsafe_allow_html=True,
    )
    events = state.trace_events[-8:] or []
    if not events:
        _render_thought_card("Plan", "Ready", "Step 0", "Tell me the trip you want. I will collect missing details and show each agent step here.", "plan")
    for event in reversed(events):
        card_type = _event_card_type(event.event_type, event.status)
        meta = f"Step {event.step} · tokens {event.tokens_used} · tools {event.tool_calls_used}"
        body = event.output_summary
        if event.error:
            body = f"{body}. {event.error}"
        _render_thought_card(card_type.title(), event.node, meta, body, card_type)
    st.markdown("</div></div>", unsafe_allow_html=True)


def _render_thought_card(card_type: str, title: str, meta: str, body: str, class_name: str) -> None:
    st.markdown(
        f"""
        <div class="tc-thought-card">
          <div class="tc-thought-header">
            <div class="tc-thought-icon tc-icon-{html.escape(class_name)}">{_thought_icon(class_name)}</div>
            <div class="tc-thought-meta">
              <div class="tc-thought-title">{html.escape(title)}</div>
              <div class="tc-thought-time">{html.escape(meta)}</div>
            </div>
            <span class="tc-thought-type tc-type-{html.escape(class_name)}">{html.escape(card_type)}</span>
          </div>
          <div class="tc-thought-body">
            <div class="tc-thought-text">{html.escape(body)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _active_step_index(state: TravelState) -> int:
    if state.current_state == WorkflowState.COMPLETE:
        return 7
    if state.current_state == WorkflowState.GENERATING_CALENDAR:
        return 6
    if state.current_state.name.startswith("AWAITING"):
        return 5
    if state.current_state == WorkflowState.REVIEWING:
        return 4
    if state.current_state == WorkflowState.BUILDING_ITINERARY:
        return 3
    if state.current_state == WorkflowState.RESEARCHING:
        return 2
    return 1


def _tool_status(settings: Settings, key: str) -> tuple[str, str]:
    if settings.has_key(key):
        return "Ready", "tc-status-done"
    if settings.allow_demo_fallbacks:
        return "Fallback", "tc-status-running"
    return "Missing", "tc-status-wait"


def _city_summary(state: TravelState) -> str:
    cities = state.destination_plan.get("cities") or []
    if cities:
        return " · ".join(f"{city.get('city')} {city.get('nights')}d" for city in cities)
    return "Calendar-ready draft"


def _active_trip(state: TravelState) -> dict:
    return state.preferences or state.user_input


def _title_text(value: object) -> str | None:
    if value in {None, ""}:
        return None
    return str(value).title()


def _date_range_label(trip: dict) -> str | None:
    start_date = trip.get("start_date")
    if not start_date:
        return None
    try:
        start = datetime.fromisoformat(str(start_date)).date()
    except ValueError:
        return str(start_date)
    days = trip.get("days")
    if not isinstance(days, int) or days < 1:
        return _format_display_date(start, include_year=True)
    end = start + timedelta(days=days)
    if start.year == end.year:
        return f"{_format_display_date(start)} - {_format_display_date(end, include_year=True)}"
    return f"{_format_display_date(start, include_year=True)} - {_format_display_date(end, include_year=True)}"


def _format_display_date(value, *, include_year: bool = False) -> str:
    formatted = value.strftime("%b %d, %Y" if include_year else "%b %d")
    return formatted.replace(" 0", " ")


def _dot_class(event_type: str) -> str:
    return {
        "flight": "tc-dot-blue",
        "hotel": "tc-dot-purple",
        "meal": "tc-dot-amber",
        "attraction": "tc-dot-teal",
    }.get(event_type, "tc-dot-muted")


def _tag_class(event_type: str) -> str:
    return {
        "flight": "tc-tag-flight",
        "hotel": "tc-tag-hotel",
        "meal": "tc-tag-food",
        "attraction": "tc-tag-attraction",
    }.get(event_type, "tc-tag-attraction")


def _event_card_type(event_type: str, status: str) -> str:
    if "tool" in event_type:
        return "tool"
    if status == "error":
        return "critique"
    if "review" in event_type:
        return "critique"
    if "decision" in event_type:
        return "decision"
    return "plan"


def _thought_icon(class_name: str) -> str:
    return {"tool": "◎", "critique": "⚠", "decision": "✓"}.get(class_name, "☷")
