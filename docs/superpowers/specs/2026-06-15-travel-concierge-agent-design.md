# Travel Concierge Agent Design

Date: 2026-06-15

## Source Inputs

This design is based on:

- `solution requirements/AI_Travel_Concierge_Codex_Instructions_v2 (1).docx`
- `ux designs/travel_concierge_ui.html`
- `ux designs/ai_travel_concierge_with_reasoning_panel.html`

The requirements document is authoritative for behavior. The HTML files are authoritative for visual direction.

## Product Experience

The application opens directly into the Travel Concierge workspace. It does not use a marketing landing page.

The UI follows the supplied HTML design closely:

- Left workflow sidebar with current state, approvals, tool activity, and session usage.
- Center workspace for trip preferences, itinerary generation, approval prompts, review results, and downloads.
- Right trace/debug panel with structured agent activity and reasoning summaries.

The design keeps the supplied visual language: muted warm page background, white app shell, compact typography, restrained badges, itinerary rows, approval panels, 8px-style controls, and reasoning cards.

The UI sample shows "Approval gate 1 of 3", but the requirements document defines five approval gates. The implemented UI will use five gates:

1. Preference confirmation.
2. Destination/city split approval.
3. High-risk day approval when tradeoffs or overloaded days exist.
4. Final itinerary approval.
5. Calendar creation approval before ICS export.

The trace/debug panel must not expose private chain-of-thought. It will show concise structured summaries: node starts and completions, tool calls, decisions, retries, review scores, loop counts, token estimates, fallback/live mode, and errors.

## Architecture

The app will use Polished Streamlit plus Modular LangGraph.

The project structure will be:

```text
streamlit_app.py
src/
  agents/
    preference_agent.py
    itinerary_agent.py
    review_agent.py
    approval_agent.py
  graph/
    travel_graph.py
    nodes.py
  tools/
    serpapi_tools.py
    tavily_tools.py
    google_places_tools.py
    google_maps_tools.py
    calendar_tools.py
  state/
    travel_state.py
  observability/
    trace_logger.py
    token_tracker.py
  prompts/
    preference_prompt.py
    itinerary_prompt.py
    review_prompt.py
  ui/
    components.py
    styles.py
  config/
    settings.py
  exports/
    itinerary_export.py
tests/
  test_calendar_export.py
  test_fallback_policy.py
  test_graph_flow.py
  test_loop_controls.py
  test_trace_logger.py
requirements.txt
.streamlit/config.toml
.env.example
README.md
```

`streamlit_app.py` owns rendering, user interaction, Streamlit session state, and download buttons. Agent and graph logic live under `src/`.

`src/graph/` defines the LangGraph workflow and state transitions. Each graph node has a bounded responsibility: preference collection, research, destination approval, itinerary generation, review, approval handling, calendar generation, and completion/failure handling.

`src/state/` defines a typed `TravelState` model containing user inputs, preferences, research results, itinerary items, approvals, counters, trace events, generated artifacts, and the current workflow state.

`src/tools/` wraps OpenAI, SerpAPI, Tavily, Google Places, Google Maps, and ICS generation.

`src/observability/` provides structured trace logging and token/tool counters. These events feed both the UI reasoning panel and downloadable JSON trace.

## Runtime Modes

The app supports live APIs when credentials are available and demo/mock fallbacks when explicitly allowed.

The controlling setting is:

```text
ALLOW_DEMO_FALLBACKS=true|false
```

Tool behavior:

- If live credentials exist, the tool attempts the live API.
- If live API fails and `ALLOW_DEMO_FALLBACKS=true`, the tool returns clearly labeled fallback data and logs the fallback.
- If live API fails and `ALLOW_DEMO_FALLBACKS=false`, the node fails with a traceable error and the workflow pauses or stops according to the state transition.
- If credentials are missing and `ALLOW_DEMO_FALLBACKS=true`, the tool uses labeled fallback data.
- If credentials are missing and `ALLOW_DEMO_FALLBACKS=false`, the tool fails strictly.

The UI must show the active mode and each tool's live/fallback/error status.

Required live credentials:

```text
OPENAI_API_KEY
SERPAPI_API_KEY
TAVILY_API_KEY
GOOGLE_MAPS_API_KEY
```

## Data Flow

The primary graph flow is:

```text
COLLECTING_REQUIREMENTS
-> AWAITING_PREFERENCE_APPROVAL
-> RESEARCHING
-> AWAITING_DESTINATION_APPROVAL
-> BUILDING_ITINERARY
-> REVIEWING
-> AWAITING_HIGH_RISK_DAY_APPROVAL? 
-> AWAITING_ITINERARY_APPROVAL
-> AWAITING_CALENDAR_APPROVAL
-> GENERATING_CALENDAR
-> COMPLETE
```

`AWAITING_HIGH_RISK_DAY_APPROVAL` is conditional. It appears when review finds overloaded days, budget tradeoffs, dietary uncertainty, or routing compromises that need human judgment.

Failure states must be traceable and recoverable where practical. Users should be able to continue with partial results in fallback mode or simplify the trip when a control limit is reached.

## Session Memory

Version 1 uses Streamlit session state as live memory. No database is included.

Stored in `st.session_state`:

- `TravelState`.
- Chat/messages.
- Pending approval payload.
- Trace events.
- Current rendered itinerary.
- Generated ICS bytes.
- Generated trace JSON bytes.

Generated artifacts should be kept in memory where possible and exposed through Streamlit download buttons. The filesystem is used only for short-lived temporary files when a library requires a file path.

This means refreshes or Streamlit Cloud restarts can reset active trips. Users can download the itinerary, ICS file, and trace JSON before leaving.

## Operational Controls

The following controls are core requirements:

- Planner iterations: maximum 3.
- Review cycles: maximum 3.
- Tool retries: maximum 2 per failed tool call.
- Total tool calls: maximum 25 per session.
- Session token budget: 100,000 estimated tokens.
- At 95% token budget, pause and ask the user whether to approve current state or continue.
- No booking, payments, reservations, direct calendar modification, or irreversible external writes.

Loop rule:

```text
IF review_score < 8 AND review_iteration_count < 3:
    return to BUILDING_ITINERARY
ELSE IF review_score < 8 AND review_iteration_count >= 3:
    transition to AWAITING_ITINERARY_APPROVAL with explanation
ELSE:
    transition to AWAITING_ITINERARY_APPROVAL
```

When a control limit is reached, the graph pauses and asks the user whether to accept partial results, simplify the plan, or stop.

## UI Implementation

The Streamlit UI layer will live in `src/ui/`.

It will include:

- CSS theme based on the supplied HTML palette, spacing, and compact visual style.
- Reusable render functions for workflow sidebar, preference cards, itinerary rows, approval panels, trace cards, badges, status indicators, and download actions.
- Streamlit-native controls for forms, buttons, chat input, approval choices, and downloads.
- Responsive behavior for smaller screens. The side panels may stack beneath the main itinerary while preserving the design language.

The UI will expose:

- Environment status: live/fallback/strict mode, missing keys, and tool readiness.
- Workflow state and approval progress.
- Tool activity and failure/retry status.
- Review scores and critique summaries.
- Download buttons for itinerary, ICS calendar file, and trace JSON.

## Calendar Export

ICS generation occurs only after final itinerary approval and calendar creation approval.

Each calendar event includes:

- Title.
- Start time.
- End time.
- Location.
- Description.
- Duration.
- Notes.
- Estimated cost when available.
- Rationale or source summary when available.
- Backup option when available.

Event types include flights, hotel check-in/out, attractions, meals, transit, and buffers.

## Error Handling

The app prefers graceful degradation when fallback mode is enabled and strict failure when fallback mode is disabled.

Expected behavior:

- Missing required user details trigger follow-up questions before research.
- Failed tools retry twice.
- If fallback mode is enabled, failed or unavailable tools return labeled fallback data.
- If fallback mode is disabled, failed or unavailable tools halt the relevant node with a visible traceable error.
- Budget or dietary conflicts are called out and routed to user approval or revision.
- Loop and token limits pause the graph instead of continuing silently.

## Testing

Initial tests will cover:

- State initialization and graph transitions.
- Fallback/live policy behavior.
- Loop limits and tool-call limits.
- Review score threshold behavior.
- ICS event generation.
- Trace event schema.

Integration tests that require real credentials will be skippable. Fallback fixtures will allow local and CI verification without external API keys.

## Deployment

The repository will be prepared for Streamlit Cloud with:

- `requirements.txt`.
- `.streamlit/config.toml`.
- `.env.example`.
- `README.md`.
- `streamlit_app.py` as the entrypoint.

Secrets for Streamlit Cloud:

```text
OPENAI_API_KEY
SERPAPI_API_KEY
TAVILY_API_KEY
GOOGLE_MAPS_API_KEY
ALLOW_DEMO_FALLBACKS
```

## Open Decisions

No open product decisions remain for the design phase. The user approved:

- Polished Streamlit plus Modular LangGraph.
- Live APIs when available with an explicit fallback flag.
- Strict behavior when `ALLOW_DEMO_FALLBACKS=false`.
- In-memory Streamlit session state for version 1.
- UI should stay true to the supplied design.
- Five approval gates from the requirements document.
