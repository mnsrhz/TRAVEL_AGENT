# Travel Concierge Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished Streamlit Cloud Travel Concierge Agent with modular LangGraph workflow, five approval gates, live-or-fallback tools, trace/debug visibility, and ICS export.

**Architecture:** Streamlit owns UI and session state while `src/` owns domain state, graph nodes, tool adapters, observability, exports, and reusable UI renderers. Build fallback-mode behavior first so the app is testable without external credentials, then wire live adapters behind the same policy. Keep every node bounded and traceable.

**Tech Stack:** Python 3.11+, Streamlit, LangGraph, LangChain OpenAI, Pydantic, python-dotenv, requests, google-search-results, tavily-python, googlemaps, icalendar, pytest.

---

## File Structure

- Create `streamlit_app.py`: Streamlit entrypoint, session bootstrap, page orchestration, user interactions, download buttons.
- Create `requirements.txt`: Streamlit Cloud and test dependencies.
- Create `.streamlit/config.toml`: Streamlit page/server defaults.
- Create `.env.example`: documented secrets and runtime flags.
- Create `README.md`: setup, local run, Streamlit Cloud deployment, fallback behavior.
- Create package markers: `src/__init__.py`, `src/agents/__init__.py`, `src/config/__init__.py`, `src/exports/__init__.py`, `src/graph/__init__.py`, `src/observability/__init__.py`, `src/prompts/__init__.py`, `src/state/__init__.py`, `src/tools/__init__.py`, `src/ui/__init__.py`.
- Create `src/config/settings.py`: environment parsing, fallback flag, API key readiness.
- Create `src/state/travel_state.py`: typed state enums and dataclasses/Pydantic models.
- Create `src/observability/trace_logger.py`: trace event schema and append/export helpers.
- Create `src/observability/token_tracker.py`: simple estimated token accounting.
- Create `src/tools/fallback_data.py`: deterministic demo data for Japan trip flow.
- Create `src/tools/policy.py`: live/fallback/strict tool execution policy.
- Create `src/tools/serpapi_tools.py`: flight/hotel search adapter.
- Create `src/tools/tavily_tools.py`: attractions research adapter.
- Create `src/tools/google_places_tools.py`: restaurant adapter.
- Create `src/tools/google_maps_tools.py`: transit adapter.
- Create `src/tools/calendar_tools.py`: ICS generation.
- Create `src/agents/preference_agent.py`: required preference checks and normalization.
- Create `src/agents/itinerary_agent.py`: itinerary generation using research data.
- Create `src/agents/review_agent.py`: deterministic review scoring and risk detection.
- Create `src/agents/approval_agent.py`: approval payload creation and application.
- Create `src/prompts/preference_prompt.py`, `src/prompts/itinerary_prompt.py`, `src/prompts/review_prompt.py`: prompt constants for future live LLM refinement.
- Create `src/graph/nodes.py`: graph node functions.
- Create `src/graph/travel_graph.py`: LangGraph compile function and fallback sequential runner if LangGraph import is unavailable during tests.
- Create `src/ui/styles.py`: CSS matching supplied HTML design.
- Create `src/ui/components.py`: reusable UI renderers.
- Create `src/exports/itinerary_export.py`: markdown/text itinerary and trace JSON exports.
- Create tests: `tests/test_settings.py`, `tests/test_trace_logger.py`, `tests/test_fallback_policy.py`, `tests/test_loop_controls.py`, `tests/test_calendar_export.py`, `tests/test_graph_flow.py`, `tests/test_review_agent.py`.

---

### Task 1: Project Skeleton And Settings

**Files:**
- Create: `requirements.txt`
- Create: `.streamlit/config.toml`
- Create: `.env.example`
- Create: `src/__init__.py` and package marker files
- Create: `src/config/settings.py`
- Test: `tests/test_settings.py`

- [ ] **Step 1: Write the failing settings tests**

Create `tests/test_settings.py`:

```python
from src.config.settings import Settings


def test_settings_defaults_to_strict_mode_when_flag_missing(monkeypatch):
    monkeypatch.delenv("ALLOW_DEMO_FALLBACKS", raising=False)
    settings = Settings.from_env()
    assert settings.allow_demo_fallbacks is False
    assert settings.mode_label == "Strict live"


def test_settings_parses_fallback_flag(monkeypatch):
    monkeypatch.setenv("ALLOW_DEMO_FALLBACKS", "true")
    settings = Settings.from_env()
    assert settings.allow_demo_fallbacks is True
    assert settings.mode_label == "Live + fallback"


def test_settings_reports_missing_keys(monkeypatch):
    for key in ("OPENAI_API_KEY", "SERPAPI_API_KEY", "TAVILY_API_KEY", "GOOGLE_MAPS_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    settings = Settings.from_env()
    assert settings.missing_keys == [
        "OPENAI_API_KEY",
        "SERPAPI_API_KEY",
        "TAVILY_API_KEY",
        "GOOGLE_MAPS_API_KEY",
    ]
    assert settings.has_key("OPENAI_API_KEY") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_settings.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'src.config'`.

- [ ] **Step 3: Create dependencies and config files**

Create `requirements.txt`:

```text
streamlit>=1.36
langgraph>=0.2
langchain>=0.2
langchain-openai>=0.1
pydantic>=2.7
python-dotenv>=1.0
requests>=2.32
google-search-results>=2.4
tavily-python>=0.3
googlemaps>=4.10
icalendar>=5.0
pytest>=8.2
```

Create `.streamlit/config.toml`:

```toml
[browser]
gatherUsageStats = false

[server]
headless = true

[theme]
base = "light"
primaryColor = "#185FA5"
backgroundColor = "#e8e6e0"
secondaryBackgroundColor = "#f7f7f5"
textColor = "#1a1a18"
```

Create `.env.example`:

```text
OPENAI_API_KEY=
SERPAPI_API_KEY=
TAVILY_API_KEY=
GOOGLE_MAPS_API_KEY=
ALLOW_DEMO_FALLBACKS=true
```

- [ ] **Step 4: Add package markers**

Create empty files:

```text
src/__init__.py
src/agents/__init__.py
src/config/__init__.py
src/exports/__init__.py
src/graph/__init__.py
src/observability/__init__.py
src/prompts/__init__.py
src/state/__init__.py
src/tools/__init__.py
src/ui/__init__.py
```

- [ ] **Step 5: Implement settings**

Create `src/config/settings.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass


REQUIRED_API_KEYS = (
    "OPENAI_API_KEY",
    "SERPAPI_API_KEY",
    "TAVILY_API_KEY",
    "GOOGLE_MAPS_API_KEY",
)


def _parse_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    serpapi_api_key: str | None
    tavily_api_key: str | None
    google_maps_api_key: str | None
    allow_demo_fallbacks: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            serpapi_api_key=os.getenv("SERPAPI_API_KEY") or None,
            tavily_api_key=os.getenv("TAVILY_API_KEY") or None,
            google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY") or None,
            allow_demo_fallbacks=_parse_bool(os.getenv("ALLOW_DEMO_FALLBACKS")),
        )

    @property
    def mode_label(self) -> str:
        return "Live + fallback" if self.allow_demo_fallbacks else "Strict live"

    @property
    def key_map(self) -> dict[str, str | None]:
        return {
            "OPENAI_API_KEY": self.openai_api_key,
            "SERPAPI_API_KEY": self.serpapi_api_key,
            "TAVILY_API_KEY": self.tavily_api_key,
            "GOOGLE_MAPS_API_KEY": self.google_maps_api_key,
        }

    @property
    def missing_keys(self) -> list[str]:
        return [key for key, value in self.key_map.items() if not value]

    def has_key(self, key: str) -> bool:
        return bool(self.key_map.get(key))
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_settings.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .streamlit/config.toml .env.example src tests/test_settings.py
git commit -m "feat: add project settings"
```

---

### Task 2: State Models And Trace Logging

**Files:**
- Create: `src/state/travel_state.py`
- Create: `src/observability/trace_logger.py`
- Create: `src/observability/token_tracker.py`
- Test: `tests/test_trace_logger.py`

- [ ] **Step 1: Write failing trace/state tests**

Create `tests/test_trace_logger.py`:

```python
from src.observability.trace_logger import TraceLogger
from src.state.travel_state import TravelState, WorkflowState


def test_travel_state_defaults_to_collecting_requirements():
    state = TravelState()
    assert state.current_state == WorkflowState.COLLECTING_REQUIREMENTS
    assert state.tool_call_count == 0
    assert state.review_iteration_count == 0


def test_trace_logger_appends_structured_event():
    state = TravelState()
    logger = TraceLogger(state)
    logger.log(
        node="Preference Agent",
        event_type="node_started",
        action="collect_preferences",
        input_summary="User requested Japan trip",
        output_summary="Checking required fields",
        status="success",
    )
    assert len(state.trace_events) == 1
    event = state.trace_events[0]
    assert event.step == 1
    assert event.state == WorkflowState.COLLECTING_REQUIREMENTS
    assert event.node == "Preference Agent"
    assert event.event_type == "node_started"
    assert event.error is None


def test_trace_logger_exports_json():
    state = TravelState()
    TraceLogger(state).log(
        node="Review Agent",
        event_type="node_completed",
        action="score_itinerary",
        input_summary="Draft itinerary",
        output_summary="Score 8.5",
        status="success",
        tokens_used=120,
    )
    payload = TraceLogger(state).to_json()
    assert '"node": "Review Agent"' in payload
    assert '"tokens_used": 120' in payload
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_trace_logger.py -v`

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement state models**

Create `src/state/travel_state.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class WorkflowState(StrEnum):
    COLLECTING_REQUIREMENTS = "COLLECTING_REQUIREMENTS"
    AWAITING_PREFERENCE_APPROVAL = "AWAITING_PREFERENCE_APPROVAL"
    RESEARCHING = "RESEARCHING"
    AWAITING_DESTINATION_APPROVAL = "AWAITING_DESTINATION_APPROVAL"
    BUILDING_ITINERARY = "BUILDING_ITINERARY"
    REVIEWING = "REVIEWING"
    AWAITING_HIGH_RISK_DAY_APPROVAL = "AWAITING_HIGH_RISK_DAY_APPROVAL"
    AWAITING_ITINERARY_APPROVAL = "AWAITING_ITINERARY_APPROVAL"
    AWAITING_CALENDAR_APPROVAL = "AWAITING_CALENDAR_APPROVAL"
    GENERATING_CALENDAR = "GENERATING_CALENDAR"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@dataclass
class TraceEvent:
    step: int
    timestamp: str
    state: WorkflowState
    node: str
    event_type: str
    action: str
    input_summary: str
    output_summary: str
    decision: str | None = None
    tokens_used: int = 0
    tool_calls_used: int = 0
    loop_count: int = 0
    max_loop_count: int = 0
    status: str = "success"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        return data


@dataclass
class TravelState:
    user_input: dict[str, Any] = field(default_factory=dict)
    preferences: dict[str, Any] = field(default_factory=dict)
    destination_plan: dict[str, Any] = field(default_factory=dict)
    flights: list[dict[str, Any]] = field(default_factory=list)
    hotels: list[dict[str, Any]] = field(default_factory=list)
    attractions: list[dict[str, Any]] = field(default_factory=list)
    restaurants: list[dict[str, Any]] = field(default_factory=list)
    transit_estimates: list[dict[str, Any]] = field(default_factory=list)
    itinerary: list[dict[str, Any]] = field(default_factory=list)
    review: dict[str, Any] = field(default_factory=dict)
    approvals: dict[str, bool] = field(default_factory=dict)
    current_state: WorkflowState = WorkflowState.COLLECTING_REQUIREMENTS
    tool_call_count: int = 0
    token_count: int = 0
    review_iteration_count: int = 0
    planner_iteration_count: int = 0
    trace_events: list[TraceEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    generated_ics: bytes | None = None

    def now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
```

- [ ] **Step 4: Implement trace logger**

Create `src/observability/trace_logger.py`:

```python
from __future__ import annotations

import json

from src.state.travel_state import TraceEvent, TravelState


class TraceLogger:
    def __init__(self, state: TravelState):
        self.state = state

    def log(
        self,
        *,
        node: str,
        event_type: str,
        action: str,
        input_summary: str,
        output_summary: str,
        status: str,
        decision: str | None = None,
        tokens_used: int = 0,
        tool_calls_used: int = 0,
        loop_count: int = 0,
        max_loop_count: int = 0,
        error: str | None = None,
    ) -> TraceEvent:
        event = TraceEvent(
            step=len(self.state.trace_events) + 1,
            timestamp=self.state.now(),
            state=self.state.current_state,
            node=node,
            event_type=event_type,
            action=action,
            input_summary=input_summary,
            output_summary=output_summary,
            decision=decision,
            tokens_used=tokens_used,
            tool_calls_used=tool_calls_used,
            loop_count=loop_count,
            max_loop_count=max_loop_count,
            status=status,
            error=error,
        )
        self.state.trace_events.append(event)
        self.state.token_count += tokens_used
        self.state.tool_call_count += tool_calls_used
        if error:
            self.state.errors.append(error)
        return event

    def to_json(self) -> str:
        return json.dumps([event.to_dict() for event in self.state.trace_events], indent=2)
```

- [ ] **Step 5: Implement token tracker**

Create `src/observability/token_tracker.py`:

```python
def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text.split()) * 2)


def token_budget_status(token_count: int, budget: int = 100_000) -> dict[str, float | bool | int]:
    ratio = token_count / budget
    return {
        "used": token_count,
        "budget": budget,
        "ratio": ratio,
        "should_pause": ratio >= 0.95,
    }
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_trace_logger.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/state src/observability tests/test_trace_logger.py
git commit -m "feat: add travel state and tracing"
```

---

### Task 3: Fallback Data And Tool Policy

**Files:**
- Create: `src/tools/fallback_data.py`
- Create: `src/tools/policy.py`
- Test: `tests/test_fallback_policy.py`

- [ ] **Step 1: Write failing fallback policy tests**

Create `tests/test_fallback_policy.py`:

```python
import pytest

from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools.policy import ToolExecutionError, run_tool_with_policy


def test_policy_uses_fallback_when_key_missing_and_flag_on():
    state = TravelState()
    settings = Settings(None, None, None, None, allow_demo_fallbacks=True)

    result = run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="Tavily",
        required_key="TAVILY_API_KEY",
        live_call=lambda: [{"name": "Live"}],
        fallback_call=lambda: [{"name": "Fallback", "source": "demo"}],
        input_summary="Kyoto attractions",
    )

    assert result == [{"name": "Fallback", "source": "demo"}]
    assert state.trace_events[-1].status == "fallback"


def test_policy_raises_when_key_missing_and_strict():
    state = TravelState()
    settings = Settings(None, None, None, None, allow_demo_fallbacks=False)

    with pytest.raises(ToolExecutionError):
        run_tool_with_policy(
            state=state,
            settings=settings,
            tool_name="SerpAPI Flights",
            required_key="SERPAPI_API_KEY",
            live_call=lambda: [],
            fallback_call=lambda: [],
            input_summary="SFO to Tokyo",
        )

    assert state.current_state.value == "FAILED"
    assert "Missing SERPAPI_API_KEY" in state.errors[-1]


def test_policy_falls_back_after_live_exception_when_flag_on():
    state = TravelState()
    settings = Settings(None, "serp", None, None, allow_demo_fallbacks=True)

    result = run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="SerpAPI Hotels",
        required_key="SERPAPI_API_KEY",
        live_call=lambda: (_ for _ in ()).throw(RuntimeError("rate limited")),
        fallback_call=lambda: [{"hotel": "Demo hotel"}],
        input_summary="Tokyo hotels",
    )

    assert result == [{"hotel": "Demo hotel"}]
    assert state.trace_events[-1].status == "fallback"
    assert "rate limited" in state.trace_events[-1].error
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fallback_policy.py -v`

Expected: FAIL with missing `src.tools.policy`.

- [ ] **Step 3: Implement fallback data**

Create `src/tools/fallback_data.py`:

```python
DEMO_DESTINATION_PLAN = {
    "title": "10-day Japan - Tokyo, Kyoto, Osaka",
    "cities": [
        {"city": "Tokyo", "days": 4, "rationale": "Arrival hub, neighborhoods, food, and museums."},
        {"city": "Kyoto", "days": 3, "rationale": "Temples, shrines, and traditional districts."},
        {"city": "Osaka", "days": 3, "rationale": "Food, day trips, and departure flexibility."},
    ],
    "source": "demo",
}

DEMO_FLIGHTS = [
    {
        "title": "SFO to Tokyo - ANA demo option",
        "airline": "ANA",
        "price": 820,
        "duration": "11h 20m",
        "source": "demo",
    }
]

DEMO_HOTELS = [
    {"name": "Shinjuku Granbell Hotel", "city": "Tokyo", "nightly_price": 140, "rating": 4.2, "source": "demo"},
    {"name": "Kyoto Granbell Hotel", "city": "Kyoto", "nightly_price": 130, "rating": 4.4, "source": "demo"},
    {"name": "Hotel The Flag Shinsaibashi", "city": "Osaka", "nightly_price": 120, "rating": 4.5, "source": "demo"},
]

DEMO_ATTRACTIONS = [
    {"name": "Senso-ji Temple", "city": "Tokyo", "duration_hours": 2, "source": "demo"},
    {"name": "Shibuya Crossing and Harajuku", "city": "Tokyo", "duration_hours": 3, "source": "demo"},
    {"name": "Fushimi Inari Taisha", "city": "Kyoto", "duration_hours": 3, "source": "demo"},
    {"name": "Dotonbori", "city": "Osaka", "duration_hours": 2, "source": "demo"},
]

DEMO_RESTAURANTS = [
    {"name": "Vegan Ramen UZU", "city": "Tokyo", "dietary": "vegetarian", "rating": 4.5, "source": "demo"},
    {"name": "TowZen", "city": "Kyoto", "dietary": "vegetarian", "rating": 4.6, "source": "demo"},
    {"name": "Paprika Shokudo", "city": "Osaka", "dietary": "vegetarian", "rating": 4.4, "source": "demo"},
]

DEMO_TRANSIT = [
    {"origin": "Shinjuku", "destination": "Asakusa", "duration_minutes": 35, "mode": "metro", "source": "demo"},
    {"origin": "Kyoto Station", "destination": "Fushimi Inari", "duration_minutes": 15, "mode": "train", "source": "demo"},
]
```

- [ ] **Step 4: Implement tool policy**

Create `src/tools/policy.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from src.config.settings import Settings
from src.observability.trace_logger import TraceLogger
from src.state.travel_state import TravelState, WorkflowState

T = TypeVar("T")


class ToolExecutionError(RuntimeError):
    pass


def run_tool_with_policy(
    *,
    state: TravelState,
    settings: Settings,
    tool_name: str,
    required_key: str,
    live_call: Callable[[], T],
    fallback_call: Callable[[], T],
    input_summary: str,
) -> T:
    logger = TraceLogger(state)

    if not settings.has_key(required_key):
        message = f"Missing {required_key} for {tool_name}"
        if settings.allow_demo_fallbacks:
            result = fallback_call()
            logger.log(
                node=tool_name,
                event_type="tool_completed",
                action="used_demo_fallback",
                input_summary=input_summary,
                output_summary=f"{tool_name} returned labeled fallback data",
                status="fallback",
                tool_calls_used=1,
                error=message,
            )
            return result
        state.current_state = WorkflowState.FAILED
        logger.log(
            node=tool_name,
            event_type="tool_failed",
            action="missing_required_key",
            input_summary=input_summary,
            output_summary="Strict mode blocked fallback",
            status="error",
            tool_calls_used=1,
            error=message,
        )
        raise ToolExecutionError(message)

    try:
        result = live_call()
        logger.log(
            node=tool_name,
            event_type="tool_completed",
            action="live_api_call",
            input_summary=input_summary,
            output_summary=f"{tool_name} returned live data",
            status="success",
            tool_calls_used=1,
        )
        return result
    except Exception as exc:
        message = f"{tool_name} failed: {exc}"
        if settings.allow_demo_fallbacks:
            result = fallback_call()
            logger.log(
                node=tool_name,
                event_type="tool_completed",
                action="fallback_after_live_failure",
                input_summary=input_summary,
                output_summary=f"{tool_name} returned labeled fallback data",
                status="fallback",
                tool_calls_used=1,
                error=message,
            )
            return result
        state.current_state = WorkflowState.FAILED
        logger.log(
            node=tool_name,
            event_type="tool_failed",
            action="live_api_failure",
            input_summary=input_summary,
            output_summary="Strict mode blocked fallback",
            status="error",
            tool_calls_used=1,
            error=message,
        )
        raise ToolExecutionError(message) from exc
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_fallback_policy.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/tools/fallback_data.py src/tools/policy.py tests/test_fallback_policy.py
git commit -m "feat: add tool fallback policy"
```

---

### Task 4: Calendar Export

**Files:**
- Create: `src/tools/calendar_tools.py`
- Create: `src/exports/itinerary_export.py`
- Test: `tests/test_calendar_export.py`

- [ ] **Step 1: Write failing calendar tests**

Create `tests/test_calendar_export.py`:

```python
from src.exports.itinerary_export import itinerary_to_markdown
from src.tools.calendar_tools import generate_ics


def sample_itinerary():
    return [
        {
            "day": 1,
            "date": "2026-10-10",
            "events": [
                {
                    "type": "attraction",
                    "title": "Visit Senso-ji Temple",
                    "start": "2026-10-10T09:00:00",
                    "end": "2026-10-10T10:30:00",
                    "location": "Asakusa, Tokyo",
                    "description": "Free entry. Backup: Nakamise shopping street.",
                    "cost": "$0",
                    "source": "demo",
                }
            ],
        }
    ]


def test_generate_ics_contains_event_fields():
    ics_bytes = generate_ics(sample_itinerary())
    content = ics_bytes.decode("utf-8")
    assert "BEGIN:VCALENDAR" in content
    assert "SUMMARY:Visit Senso-ji Temple" in content
    assert "LOCATION:Asakusa\\, Tokyo" in content
    assert "END:VCALENDAR" in content


def test_itinerary_markdown_contains_day_and_event():
    markdown = itinerary_to_markdown(sample_itinerary())
    assert "## Day 1 - 2026-10-10" in markdown
    assert "Visit Senso-ji Temple" in markdown
    assert "Asakusa, Tokyo" in markdown
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_calendar_export.py -v`

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement ICS generation**

Create `src/tools/calendar_tools.py`:

```python
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from icalendar import Calendar, Event


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def generate_ics(itinerary: list[dict]) -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//Travel Concierge Agent//streamlit//")
    calendar.add("version", "2.0")

    for day in itinerary:
        for item in day.get("events", []):
            event = Event()
            event.add("uid", f"{uuid4()}@travel-concierge")
            event.add("summary", item["title"])
            event.add("dtstart", _parse_dt(item["start"]))
            event.add("dtend", _parse_dt(item["end"]))
            event.add("location", item.get("location", ""))
            description = item.get("description", "")
            cost = item.get("cost")
            source = item.get("source")
            notes = [description]
            if cost:
                notes.append(f"Estimated cost: {cost}")
            if source:
                notes.append(f"Source: {source}")
            event.add("description", "\n".join(part for part in notes if part))
            calendar.add_component(event)

    return calendar.to_ical()
```

- [ ] **Step 4: Implement markdown export**

Create `src/exports/itinerary_export.py`:

```python
from __future__ import annotations

import json

from src.state.travel_state import TravelState


def itinerary_to_markdown(itinerary: list[dict]) -> str:
    lines = ["# Travel Itinerary", ""]
    for day in itinerary:
        lines.append(f"## Day {day['day']} - {day['date']}")
        for event in day.get("events", []):
            lines.append(f"- **{event['title']}** ({event['start']} to {event['end']})")
            if event.get("location"):
                lines.append(f"  - Location: {event['location']}")
            if event.get("description"):
                lines.append(f"  - Notes: {event['description']}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def trace_to_json_bytes(state: TravelState) -> bytes:
    return json.dumps([event.to_dict() for event in state.trace_events], indent=2).encode("utf-8")
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_calendar_export.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/tools/calendar_tools.py src/exports/itinerary_export.py tests/test_calendar_export.py
git commit -m "feat: add itinerary and calendar exports"
```

---

### Task 5: Preference, Itinerary, Review, And Approval Agents

**Files:**
- Create: `src/agents/preference_agent.py`
- Create: `src/agents/itinerary_agent.py`
- Create: `src/agents/review_agent.py`
- Create: `src/agents/approval_agent.py`
- Create: `src/prompts/preference_prompt.py`
- Create: `src/prompts/itinerary_prompt.py`
- Create: `src/prompts/review_prompt.py`
- Test: `tests/test_review_agent.py`
- Test: `tests/test_loop_controls.py`

- [ ] **Step 1: Write failing agent tests**

Create `tests/test_review_agent.py`:

```python
from src.agents.itinerary_agent import build_demo_itinerary
from src.agents.review_agent import review_itinerary


def test_review_flags_overloaded_moderate_day():
    itinerary = [
        {
            "day": 1,
            "date": "2026-10-10",
            "events": [
                {"type": "attraction", "title": "A", "start": "2026-10-10T09:00:00", "end": "2026-10-10T10:00:00"},
                {"type": "attraction", "title": "B", "start": "2026-10-10T11:00:00", "end": "2026-10-10T12:00:00"},
                {"type": "attraction", "title": "C", "start": "2026-10-10T13:00:00", "end": "2026-10-10T14:00:00"},
                {"type": "attraction", "title": "D", "start": "2026-10-10T15:00:00", "end": "2026-10-10T16:00:00"},
            ],
        }
    ]
    review = review_itinerary(itinerary, {"pace": "moderate", "dietary": "vegetarian"})
    assert review["score"] < 8
    assert review["requires_high_risk_approval"] is True
    assert "overloaded" in review["findings"][0].lower()


def test_demo_itinerary_has_calendar_ready_events():
    itinerary = build_demo_itinerary({"start_date": "2026-10-10", "dietary": "vegetarian"})
    assert len(itinerary) == 10
    first_event = itinerary[0]["events"][0]
    assert {"title", "start", "end", "location", "description"}.issubset(first_event)
```

Create `tests/test_loop_controls.py`:

```python
from src.agents.review_agent import next_state_after_review
from src.state.travel_state import WorkflowState


def test_low_score_under_limit_returns_to_builder():
    assert next_state_after_review(score=7.0, review_iteration_count=1) == WorkflowState.BUILDING_ITINERARY


def test_low_score_at_limit_goes_to_approval_with_explanation():
    assert next_state_after_review(score=7.0, review_iteration_count=3) == WorkflowState.AWAITING_ITINERARY_APPROVAL


def test_passing_score_goes_to_approval():
    assert next_state_after_review(score=8.5, review_iteration_count=1) == WorkflowState.AWAITING_ITINERARY_APPROVAL
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_review_agent.py tests/test_loop_controls.py -v`

Expected: FAIL with missing agent modules.

- [ ] **Step 3: Implement preference agent**

Create `src/agents/preference_agent.py`:

```python
REQUIRED_FIELDS = ("destination", "days", "origin", "start_date", "budget", "pace", "dietary")


def missing_required_fields(user_input: dict) -> list[str]:
    return [field for field in REQUIRED_FIELDS if not user_input.get(field)]


def normalize_preferences(user_input: dict) -> dict:
    preferences = dict(user_input)
    preferences["days"] = int(preferences.get("days", 10))
    preferences["budget"] = int(str(preferences.get("budget", "3500")).replace("$", "").replace(",", ""))
    preferences["pace"] = preferences.get("pace", "moderate").lower()
    preferences["dietary"] = preferences.get("dietary", "none").lower()
    return preferences
```

- [ ] **Step 4: Implement itinerary agent**

Create `src/agents/itinerary_agent.py`:

```python
from __future__ import annotations

from datetime import datetime, timedelta


def _event(day: datetime, start_hour: int, duration_hours: float, title: str, location: str, event_type: str) -> dict:
    start = day.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=int(duration_hours * 60))
    return {
        "type": event_type,
        "title": title,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "location": location,
        "description": "Calendar-ready recommendation with estimated timing, rationale, and fallback option.",
        "cost": "$0-$80",
        "source": "demo",
    }


def build_demo_itinerary(preferences: dict) -> list[dict]:
    start_date = datetime.fromisoformat(preferences.get("start_date", "2026-10-10"))
    city_by_day = ["Tokyo"] * 4 + ["Kyoto"] * 3 + ["Osaka"] * 3
    highlights = {
        "Tokyo": ["Senso-ji Temple", "Shibuya Crossing", "Harajuku walk"],
        "Kyoto": ["Fushimi Inari Taisha", "Gion district", "Kiyomizu-dera"],
        "Osaka": ["Dotonbori", "Osaka Castle", "Kuromon Market"],
    }
    itinerary = []
    for index, city in enumerate(city_by_day):
        day = start_date + timedelta(days=index)
        names = highlights[city]
        itinerary.append(
            {
                "day": index + 1,
                "date": day.date().isoformat(),
                "city": city,
                "events": [
                    _event(day, 9, 2, names[index % len(names)], city, "attraction"),
                    _event(day, 12, 1, f"Vegetarian lunch in {city}", city, "meal"),
                    _event(day, 14, 2, f"{city} neighborhood exploration", city, "attraction"),
                ],
            }
        )
    return itinerary
```

- [ ] **Step 5: Implement review agent**

Create `src/agents/review_agent.py`:

```python
from src.state.travel_state import WorkflowState


def review_itinerary(itinerary: list[dict], preferences: dict) -> dict:
    findings: list[str] = []
    score = 9.0
    pace = preferences.get("pace", "moderate")

    for day in itinerary:
        major_events = [event for event in day.get("events", []) if event.get("type") == "attraction"]
        if pace != "packed" and len(major_events) > 3:
            score -= 2
            findings.append(f"Day {day.get('day')} is overloaded for a {pace} pace traveler.")

    dietary = preferences.get("dietary", "none")
    if dietary not in {"none", "", None}:
        meal_events = [event for day in itinerary for event in day.get("events", []) if event.get("type") == "meal"]
        if not meal_events:
            score -= 1
            findings.append("Dietary preference is present but no meal events were planned.")

    score = max(1.0, min(10.0, score))
    return {
        "score": score,
        "findings": findings or ["Itinerary is realistic, geographically sensible, and calendar-ready."],
        "requires_high_risk_approval": bool(findings),
    }


def next_state_after_review(score: float, review_iteration_count: int) -> WorkflowState:
    if score < 8 and review_iteration_count < 3:
        return WorkflowState.BUILDING_ITINERARY
    return WorkflowState.AWAITING_ITINERARY_APPROVAL
```

- [ ] **Step 6: Implement approval agent**

Create `src/agents/approval_agent.py`:

```python
from src.state.travel_state import TravelState


APPROVAL_GATES = (
    "preference_confirmation",
    "destination_city_split",
    "high_risk_day",
    "final_itinerary",
    "calendar_creation",
)


def approve(state: TravelState, gate: str) -> None:
    if gate not in APPROVAL_GATES:
        raise ValueError(f"Unknown approval gate: {gate}")
    state.approvals[gate] = True


def is_approved(state: TravelState, gate: str) -> bool:
    return state.approvals.get(gate) is True
```

- [ ] **Step 7: Add prompt constants**

Create `src/prompts/preference_prompt.py`:

```python
PREFERENCE_SYSTEM_PROMPT = "Collect missing travel requirements and normalize preferences into structured state."
```

Create `src/prompts/itinerary_prompt.py`:

```python
ITINERARY_SYSTEM_PROMPT = "Generate a realistic day-by-day itinerary with meals, transit, timing, costs, and backups."
```

Create `src/prompts/review_prompt.py`:

```python
REVIEW_SYSTEM_PROMPT = "Score itinerary quality without exposing private chain-of-thought; return concise findings."
```

- [ ] **Step 8: Run tests**

Run: `pytest tests/test_review_agent.py tests/test_loop_controls.py -v`

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add src/agents src/prompts tests/test_review_agent.py tests/test_loop_controls.py
git commit -m "feat: add planning agents"
```

---

### Task 6: Tool Adapters

**Files:**
- Create: `src/tools/serpapi_tools.py`
- Create: `src/tools/tavily_tools.py`
- Create: `src/tools/google_places_tools.py`
- Create: `src/tools/google_maps_tools.py`
- Test: extend `tests/test_fallback_policy.py`

- [ ] **Step 1: Add adapter fallback tests**

Append to `tests/test_fallback_policy.py`:

```python
from src.tools.google_maps_tools import estimate_transit
from src.tools.google_places_tools import search_restaurants
from src.tools.serpapi_tools import search_flights, search_hotels
from src.tools.tavily_tools import search_attractions


def test_tool_adapters_return_fallback_data_when_enabled():
    settings = Settings(None, None, None, None, allow_demo_fallbacks=True)
    state = TravelState()
    assert search_flights(state, settings, {"origin": "SFO", "destination": "Tokyo"})
    assert search_hotels(state, settings, {"destination": "Tokyo"})
    assert search_attractions(state, settings, {"destination": "Japan"})
    assert search_restaurants(state, settings, {"city": "Tokyo", "dietary": "vegetarian"})
    assert estimate_transit(state, settings, {"origin": "Shinjuku", "destination": "Asakusa"})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fallback_policy.py::test_tool_adapters_return_fallback_data_when_enabled -v`

Expected: FAIL with missing adapter modules.

- [ ] **Step 3: Implement SerpAPI adapter**

Create `src/tools/serpapi_tools.py`:

```python
import requests

from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools import fallback_data
from src.tools.policy import run_tool_with_policy


def search_flights(state: TravelState, settings: Settings, query: dict) -> list[dict]:
    return run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="SerpAPI Flights",
        required_key="SERPAPI_API_KEY",
        live_call=lambda: _serpapi_search(
            settings,
            {
                "engine": "google_flights",
                "departure_id": query.get("origin"),
                "arrival_id": query.get("destination"),
                "outbound_date": query.get("start_date"),
                "currency": "USD",
            },
        ),
        fallback_call=lambda: fallback_data.DEMO_FLIGHTS,
        input_summary=f"{query.get('origin')} to {query.get('destination')}",
    )


def search_hotels(state: TravelState, settings: Settings, query: dict) -> list[dict]:
    return run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="SerpAPI Hotels",
        required_key="SERPAPI_API_KEY",
        live_call=lambda: _serpapi_search(
            settings,
            {
                "engine": "google_hotels",
                "q": f"hotels in {query.get('destination')}",
                "currency": "USD",
            },
        ),
        fallback_call=lambda: fallback_data.DEMO_HOTELS,
        input_summary=f"Hotels in {query.get('destination')}",
    )


def _serpapi_search(settings: Settings, params: dict) -> list[dict]:
    response = requests.get(
        "https://serpapi.com/search.json",
        params={**params, "api_key": settings.serpapi_api_key},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if params["engine"] == "google_flights":
        return data.get("best_flights") or data.get("other_flights") or []
    return data.get("properties") or []
```

- [ ] **Step 4: Implement Tavily adapter**

Create `src/tools/tavily_tools.py`:

```python
from tavily import TavilyClient

from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools import fallback_data
from src.tools.policy import run_tool_with_policy


def search_attractions(state: TravelState, settings: Settings, query: dict) -> list[dict]:
    return run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="Tavily Attractions",
        required_key="TAVILY_API_KEY",
        live_call=lambda: _search_tavily(settings, query),
        fallback_call=lambda: fallback_data.DEMO_ATTRACTIONS,
        input_summary=f"Attractions for {query.get('destination')}",
    )


def _search_tavily(settings: Settings, query: dict) -> list[dict]:
    client = TavilyClient(api_key=settings.tavily_api_key)
    response = client.search(
        query=f"best attractions and local travel tips for {query.get('destination')}",
        max_results=8,
        search_depth="basic",
    )
    return [
        {
            "name": item.get("title", "Attraction research result"),
            "url": item.get("url"),
            "summary": item.get("content", ""),
            "source": "tavily",
        }
        for item in response.get("results", [])
    ]
```

- [ ] **Step 5: Implement Google Places adapter**

Create `src/tools/google_places_tools.py`:

```python
import googlemaps

from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools import fallback_data
from src.tools.policy import run_tool_with_policy


def search_restaurants(state: TravelState, settings: Settings, query: dict) -> list[dict]:
    return run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="Google Places Restaurants",
        required_key="GOOGLE_MAPS_API_KEY",
        live_call=lambda: _search_places(settings, query),
        fallback_call=lambda: fallback_data.DEMO_RESTAURANTS,
        input_summary=f"{query.get('dietary')} restaurants in {query.get('city')}",
    )


def _search_places(settings: Settings, query: dict) -> list[dict]:
    client = googlemaps.Client(key=settings.google_maps_api_key)
    text = f"{query.get('dietary', '')} restaurants in {query.get('city')}"
    response = client.places(query=text, type="restaurant")
    return [
        {
            "name": item.get("name"),
            "city": query.get("city"),
            "rating": item.get("rating"),
            "address": item.get("formatted_address"),
            "place_id": item.get("place_id"),
            "source": "google_places",
        }
        for item in response.get("results", [])[:8]
    ]
```

- [ ] **Step 6: Implement Google Maps adapter**

Create `src/tools/google_maps_tools.py`:

```python
import googlemaps

from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools import fallback_data
from src.tools.policy import run_tool_with_policy


def estimate_transit(state: TravelState, settings: Settings, query: dict) -> list[dict]:
    return run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="Google Maps Transit",
        required_key="GOOGLE_MAPS_API_KEY",
        live_call=lambda: _estimate_google_transit(settings, query),
        fallback_call=lambda: fallback_data.DEMO_TRANSIT,
        input_summary=f"{query.get('origin')} to {query.get('destination')}",
    )


def _estimate_google_transit(settings: Settings, query: dict) -> list[dict]:
    client = googlemaps.Client(key=settings.google_maps_api_key)
    response = client.distance_matrix(
        origins=[query.get("origin")],
        destinations=[query.get("destination")],
        mode=query.get("mode", "transit"),
    )
    element = response["rows"][0]["elements"][0]
    if element.get("status") != "OK":
        raise RuntimeError(f"Google Maps returned {element.get('status')}")
    return [
        {
            "origin": query.get("origin"),
            "destination": query.get("destination"),
            "duration_minutes": round(element["duration"]["value"] / 60),
            "distance": element.get("distance", {}).get("text"),
            "mode": query.get("mode", "transit"),
            "source": "google_maps",
        }
    ]
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/test_fallback_policy.py -v`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/tools tests/test_fallback_policy.py
git commit -m "feat: add travel research adapters"
```

---

### Task 7: Graph Nodes And Flow

**Files:**
- Create: `src/graph/nodes.py`
- Create: `src/graph/travel_graph.py`
- Test: `tests/test_graph_flow.py`

- [ ] **Step 1: Write failing graph flow test**

Create `tests/test_graph_flow.py`:

```python
from src.config.settings import Settings
from src.graph.travel_graph import run_demo_flow_until_calendar_ready
from src.state.travel_state import TravelState, WorkflowState


def test_demo_graph_reaches_calendar_approval_with_fallbacks():
    state = TravelState(
        user_input={
            "destination": "Japan",
            "days": 10,
            "origin": "SFO",
            "start_date": "2026-10-10",
            "budget": 3500,
            "pace": "moderate",
            "dietary": "vegetarian",
        }
    )
    settings = Settings(None, None, None, None, allow_demo_fallbacks=True)
    result = run_demo_flow_until_calendar_ready(state, settings)
    assert result.current_state == WorkflowState.AWAITING_CALENDAR_APPROVAL
    assert result.destination_plan["title"].startswith("10-day Japan")
    assert result.itinerary
    assert result.review["score"] >= 8
    assert result.trace_events
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph_flow.py -v`

Expected: FAIL with missing graph modules.

- [ ] **Step 3: Implement graph nodes**

Create `src/graph/nodes.py`:

```python
from src.agents.itinerary_agent import build_demo_itinerary
from src.agents.preference_agent import missing_required_fields, normalize_preferences
from src.agents.review_agent import next_state_after_review, review_itinerary
from src.config.settings import Settings
from src.observability.trace_logger import TraceLogger
from src.state.travel_state import TravelState, WorkflowState
from src.tools.fallback_data import DEMO_DESTINATION_PLAN
from src.tools.google_maps_tools import estimate_transit
from src.tools.google_places_tools import search_restaurants
from src.tools.serpapi_tools import search_flights, search_hotels
from src.tools.tavily_tools import search_attractions


def collect_preferences(state: TravelState) -> TravelState:
    logger = TraceLogger(state)
    missing = missing_required_fields(state.user_input)
    if missing:
        logger.log(
            node="Preference Agent",
            event_type="node_completed",
            action="missing_preferences",
            input_summary="User trip basics",
            output_summary=f"Missing fields: {', '.join(missing)}",
            status="needs_input",
        )
        return state
    state.preferences = normalize_preferences(state.user_input)
    state.current_state = WorkflowState.AWAITING_PREFERENCE_APPROVAL
    logger.log(
        node="Preference Agent",
        event_type="node_completed",
        action="normalized_preferences",
        input_summary="User trip basics",
        output_summary="Preferences ready for approval",
        status="success",
    )
    return state


def research_options(state: TravelState, settings: Settings) -> TravelState:
    state.current_state = WorkflowState.RESEARCHING
    state.destination_plan = DEMO_DESTINATION_PLAN
    state.flights = search_flights(state, settings, state.preferences)
    state.hotels = search_hotels(state, settings, state.preferences)
    state.attractions = search_attractions(state, settings, state.preferences)
    state.restaurants = search_restaurants(state, settings, {"city": "Tokyo", "dietary": state.preferences.get("dietary")})
    state.transit_estimates = estimate_transit(state, settings, {"origin": "Shinjuku", "destination": "Asakusa"})
    state.current_state = WorkflowState.AWAITING_DESTINATION_APPROVAL
    TraceLogger(state).log(
        node="Research Node",
        event_type="node_completed",
        action="research_complete",
        input_summary="Travel preferences",
        output_summary="Flights, hotels, attractions, restaurants, and transit data stored",
        status="success",
    )
    return state


def build_itinerary(state: TravelState) -> TravelState:
    state.current_state = WorkflowState.BUILDING_ITINERARY
    state.planner_iteration_count += 1
    state.itinerary = build_demo_itinerary(state.preferences)
    TraceLogger(state).log(
        node="Itinerary Agent",
        event_type="node_completed",
        action="built_itinerary",
        input_summary="Research summaries",
        output_summary=f"Built {len(state.itinerary)} day itinerary",
        status="success",
        loop_count=state.planner_iteration_count,
        max_loop_count=3,
    )
    return state


def review_plan(state: TravelState) -> TravelState:
    state.current_state = WorkflowState.REVIEWING
    state.review_iteration_count += 1
    state.review = review_itinerary(state.itinerary, state.preferences)
    if state.review.get("requires_high_risk_approval"):
        state.current_state = WorkflowState.AWAITING_HIGH_RISK_DAY_APPROVAL
    else:
        state.current_state = next_state_after_review(state.review["score"], state.review_iteration_count)
    TraceLogger(state).log(
        node="Review Agent",
        event_type="node_completed",
        action="reviewed_itinerary",
        input_summary="Draft itinerary",
        output_summary=f"Score {state.review['score']}",
        decision=state.current_state.value,
        status="success",
        loop_count=state.review_iteration_count,
        max_loop_count=3,
    )
    return state
```

- [ ] **Step 4: Implement graph runner**

Create `src/graph/travel_graph.py`:

```python
from src.config.settings import Settings
from src.graph.nodes import build_itinerary, collect_preferences, research_options, review_plan
from src.state.travel_state import TravelState, WorkflowState


def run_demo_flow_until_calendar_ready(state: TravelState, settings: Settings) -> TravelState:
    collect_preferences(state)
    if state.current_state != WorkflowState.AWAITING_PREFERENCE_APPROVAL:
        return state

    state.approvals["preference_confirmation"] = True
    research_options(state, settings)
    if state.current_state != WorkflowState.AWAITING_DESTINATION_APPROVAL:
        return state

    state.approvals["destination_city_split"] = True
    build_itinerary(state)
    review_plan(state)
    if state.current_state == WorkflowState.AWAITING_HIGH_RISK_DAY_APPROVAL:
        state.approvals["high_risk_day"] = True
        state.current_state = WorkflowState.AWAITING_ITINERARY_APPROVAL

    state.approvals["final_itinerary"] = True
    state.current_state = WorkflowState.AWAITING_CALENDAR_APPROVAL
    return state
```

- [ ] **Step 5: Run graph tests**

Run: `pytest tests/test_graph_flow.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/graph tests/test_graph_flow.py
git commit -m "feat: add travel workflow graph"
```

---

### Task 8: Polished Streamlit UI Components

**Files:**
- Create: `src/ui/styles.py`
- Create: `src/ui/components.py`
- Create: `streamlit_app.py`

- [ ] **Step 1: Implement CSS theme**

Create `src/ui/styles.py`:

```python
APP_CSS = """
<style>
:root {
  --bg-primary:#ffffff; --bg-secondary:#f7f7f5; --bg-tertiary:#efede8;
  --text-primary:#1a1a18; --text-secondary:#5a5a56; --text-tertiary:#9a9a94;
  --border-light:rgba(0,0,0,0.10); --border-mid:rgba(0,0,0,0.18);
  --blue-50:#E6F1FB; --blue-600:#185FA5; --blue-800:#0C447C;
  --green-50:#EAF3DE; --green-600:#3B6D11; --green-800:#27500A;
  --amber-50:#FAEEDA; --amber-600:#854F0B; --amber-800:#633806;
  --purple-50:#EEEDFE; --purple-600:#534AB7; --purple-800:#3C3489;
  --red-50:#FCEBEB; --red-600:#A32D2D; --red-800:#791F1F;
}
.stApp { background:#e8e6e0; color:var(--text-primary); }
.block-container { max-width:1180px; padding-top:1.2rem; padding-bottom:1.2rem; }
[data-testid="stHeader"] { background:transparent; }
.tc-shell { border:0.5px solid var(--border-light); border-radius:12px; overflow:hidden; background:var(--bg-primary); }
.tc-card { border:0.5px solid var(--border-light); border-radius:8px; background:var(--bg-secondary); padding:10px 12px; margin-bottom:8px; }
.tc-label { font-size:10px; color:var(--text-tertiary); text-transform:uppercase; letter-spacing:.06em; margin-bottom:4px; }
.tc-value { font-size:12px; font-weight:600; color:var(--text-primary); }
.tc-badge { display:inline-block; font-size:10px; padding:2px 7px; border-radius:8px; font-weight:600; margin-right:4px; }
.tc-badge-blue { background:var(--blue-50); color:var(--blue-800); }
.tc-badge-green { background:var(--green-50); color:var(--green-800); }
.tc-badge-amber { background:var(--amber-50); color:var(--amber-800); }
.tc-approval { border:0.5px solid var(--border-mid); border-radius:12px; overflow:hidden; margin:10px 0; }
.tc-approval-head { background:var(--amber-50); color:var(--amber-800); padding:10px 14px; font-size:12px; font-weight:700; border-bottom:0.5px solid var(--border-light); }
.tc-approval-body { padding:12px 14px; font-size:12px; color:var(--text-secondary); }
.tc-event { display:flex; gap:10px; border-bottom:0.5px solid var(--border-light); padding:8px 4px; }
.tc-time { min-width:92px; font-size:10px; color:var(--text-tertiary); }
.tc-event-title { font-size:12px; font-weight:700; }
.tc-event-sub { font-size:11px; color:var(--text-secondary); }
.tc-trace { border:0.5px solid var(--border-light); border-radius:8px; padding:9px 11px; margin-bottom:8px; background:#fff; }
.tc-trace-title { font-size:11px; font-weight:700; }
.tc-trace-body { font-size:11px; color:var(--text-secondary); line-height:1.45; }
</style>
"""
```

- [ ] **Step 2: Implement UI renderers**

Create `src/ui/components.py`:

```python
from __future__ import annotations

import html

import streamlit as st

from src.config.settings import Settings
from src.state.travel_state import TravelState


def render_environment(settings: Settings) -> None:
    badge = "tc-badge-green" if settings.allow_demo_fallbacks else "tc-badge-amber"
    st.markdown(f'<span class="tc-badge {badge}">{settings.mode_label}</span>', unsafe_allow_html=True)
    if settings.missing_keys:
        st.caption("Missing keys: " + ", ".join(settings.missing_keys))


def render_workflow_sidebar(state: TravelState, settings: Settings) -> None:
    st.markdown("### Travel Concierge")
    st.caption("Agentic AI system")
    render_environment(settings)
    st.markdown('<div class="tc-label">Workflow</div>', unsafe_allow_html=True)
    gates = [
        ("Preference confirmation", "preference_confirmation"),
        ("Destination split", "destination_city_split"),
        ("High-risk day", "high_risk_day"),
        ("Final itinerary", "final_itinerary"),
        ("Calendar creation", "calendar_creation"),
    ]
    for label, key in gates:
        status = "Done" if state.approvals.get(key) else "Pending"
        st.markdown(
            f'<div class="tc-card"><div class="tc-value">{html.escape(label)}</div><div class="tc-label">{status}</div></div>',
            unsafe_allow_html=True,
        )
    st.metric("Tool calls", state.tool_call_count, help="Maximum 25 per session")
    st.metric("Estimated tokens", state.token_count, help="Pause at 95,000 of 100,000")


def render_preferences(state: TravelState) -> None:
    st.markdown('<div class="tc-label">Trip preferences</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for index, (label, value) in enumerate(state.preferences.items()):
        with cols[index % 2]:
            st.markdown(
                f'<div class="tc-card"><div class="tc-label">{html.escape(label)}</div><div class="tc-value">{html.escape(str(value))}</div></div>',
                unsafe_allow_html=True,
            )


def render_itinerary(state: TravelState) -> None:
    st.markdown('<div class="tc-label">Draft itinerary</div>', unsafe_allow_html=True)
    for day in state.itinerary:
        st.markdown(f"**Day {day['day']} - {day['date']} · {day.get('city', '')}**")
        for event in day.get("events", []):
            st.markdown(
                f"""
                <div class="tc-event">
                  <div class="tc-time">{html.escape(event['start'][11:16])} - {html.escape(event['end'][11:16])}</div>
                  <div>
                    <div class="tc-event-title">{html.escape(event['title'])}</div>
                    <div class="tc-event-sub">{html.escape(event.get('location', ''))}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_approval_panel(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="tc-approval">
          <div class="tc-approval-head">{html.escape(title)}</div>
          <div class="tc-approval-body">{html.escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_trace_panel(state: TravelState) -> None:
    st.markdown("### Agent reasoning")
    for event in reversed(state.trace_events[-8:]):
        st.markdown(
            f"""
            <div class="tc-trace">
              <div class="tc-trace-title">Step {event.step} · {html.escape(event.node)} · {html.escape(event.status)}</div>
              <div class="tc-trace-body">{html.escape(event.output_summary)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
```

- [ ] **Step 3: Implement Streamlit entrypoint**

Create `streamlit_app.py`:

```python
from __future__ import annotations

import streamlit as st

from src.agents.approval_agent import approve
from src.config.settings import Settings
from src.exports.itinerary_export import itinerary_to_markdown, trace_to_json_bytes
from src.graph.travel_graph import run_demo_flow_until_calendar_ready
from src.state.travel_state import TravelState, WorkflowState
from src.tools.calendar_tools import generate_ics
from src.ui.components import render_approval_panel, render_itinerary, render_preferences, render_trace_panel, render_workflow_sidebar
from src.ui.styles import APP_CSS


st.set_page_config(page_title="Travel Concierge Agent", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)


def get_state() -> TravelState:
    if "travel_state" not in st.session_state:
        st.session_state.travel_state = TravelState()
    return st.session_state.travel_state


settings = Settings.from_env()
state = get_state()

left, center, right = st.columns([0.22, 0.52, 0.26], gap="small")

with left:
    render_workflow_sidebar(state, settings)

with center:
    st.markdown("### 10-day Japan - Tokyo · Kyoto · Osaka")
    with st.form("trip_form"):
        destination = st.text_input("Destination", value=state.user_input.get("destination", "Japan"))
        days = st.number_input("Vacation days", min_value=1, max_value=30, value=int(state.user_input.get("days", 10)))
        origin = st.text_input("Origin city/airport", value=state.user_input.get("origin", "SFO"))
        start_date = st.text_input("Start date", value=state.user_input.get("start_date", "2026-10-10"))
        budget = st.number_input("Budget", min_value=0, value=int(state.user_input.get("budget", 3500)))
        pace = st.selectbox("Pace", ["relaxed", "moderate", "packed"], index=1)
        dietary = st.text_input("Dietary preference", value=state.user_input.get("dietary", "vegetarian"))
        submitted = st.form_submit_button("Start planning")

    if submitted:
        state.user_input = {
            "destination": destination,
            "days": days,
            "origin": origin,
            "start_date": start_date,
            "budget": budget,
            "pace": pace,
            "dietary": dietary,
        }
        run_demo_flow_until_calendar_ready(state, settings)
        st.rerun()

    if state.preferences:
        render_preferences(state)

    if state.itinerary:
        render_itinerary(state)
        render_approval_panel("Approval gate 5 of 5 - Calendar creation", "Approve calendar creation to generate the ICS file.")
        if st.button("Approve calendar and generate ICS", type="primary"):
            approve(state, "calendar_creation")
            state.current_state = WorkflowState.GENERATING_CALENDAR
            state.generated_ics = generate_ics(state.itinerary)
            state.current_state = WorkflowState.COMPLETE
            st.rerun()

    if state.generated_ics:
        st.download_button("Download itinerary markdown", itinerary_to_markdown(state.itinerary), file_name="travel-itinerary.md")
        st.download_button("Download calendar ICS", state.generated_ics, file_name="travel-itinerary.ics")
        st.download_button("Download trace JSON", trace_to_json_bytes(state), file_name="travel-trace.json")

with right:
    render_trace_panel(state)
```

- [ ] **Step 4: Run syntax check**

Run: `python -m py_compile streamlit_app.py src/ui/styles.py src/ui/components.py`

Expected: PASS with no output.

- [ ] **Step 5: Commit**

```bash
git add streamlit_app.py src/ui
git commit -m "feat: add polished streamlit interface"
```

---

### Task 9: README And Deployment Docs

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

Create `README.md`:

```markdown
# Travel Concierge Agent

A polished Streamlit Cloud app for planning a vacation with a bounded agentic workflow, five human approval gates, live-or-fallback travel tools, trace/debug visibility, and ICS calendar export.

## Features

- Streamlit UI modeled after the supplied Travel Concierge design.
- Modular Python source under `src/`.
- LangGraph-ready workflow nodes and typed travel state.
- Five approval gates from the requirements document.
- `ALLOW_DEMO_FALLBACKS` flag for strict live mode or live-with-demo-fallback mode.
- Event-specific `.ics` calendar export.
- Downloadable itinerary markdown and trace JSON.

## Local Setup

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/streamlit run streamlit_app.py
```

## Environment Variables

```text
OPENAI_API_KEY=
SERPAPI_API_KEY=
TAVILY_API_KEY=
GOOGLE_MAPS_API_KEY=
ALLOW_DEMO_FALLBACKS=true
```

When `ALLOW_DEMO_FALLBACKS=true`, missing or failing live tools return clearly labeled demo data. When `ALLOW_DEMO_FALLBACKS=false`, missing or failing live tools halt the workflow with a visible traceable error.

## Streamlit Cloud

1. Push this repository to GitHub.
2. Create a new Streamlit Cloud app using `streamlit_app.py` as the entrypoint.
3. Add secrets for the API keys and `ALLOW_DEMO_FALLBACKS`.
4. Deploy.

## Safety Boundaries

The app does not book flights, reserve hotels/restaurants, process payments, or modify live calendars. Calendar output is a downloadable `.ics` artifact generated only after approval.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add deployment guide"
```

---

### Task 10: Full Verification And Launch Readiness

**Files:**
- Modify only if verification exposes issues.

- [ ] **Step 1: Run all tests**

Run: `pytest -v`

Expected: all tests PASS.

- [ ] **Step 2: Run compile check**

Run: `python -m py_compile streamlit_app.py $(find src -name '*.py')`

Expected: PASS with no output.

- [ ] **Step 3: Start local Streamlit app**

Run: `.venv/bin/streamlit run streamlit_app.py`

Expected: local URL appears and the app loads.

- [ ] **Step 4: Verify manually in the browser**

Open the local Streamlit URL and confirm:

- Three-panel Travel Concierge layout appears.
- `ALLOW_DEMO_FALLBACKS` status is visible.
- Start planning creates preferences, itinerary, trace cards, and approval gate 5 of 5.
- Approving calendar creation enables itinerary markdown, ICS, and trace JSON downloads.
- No text overlaps in normal desktop width.

- [ ] **Step 5: Commit any fixes**

If verification required fixes:

```bash
git add <changed-files>
git commit -m "fix: polish launch verification issues"
```

If no fixes were required, do not create an empty commit.

---

## Self-Review

- Spec coverage: The plan covers Streamlit Cloud setup, modular source layout, typed state, fallback flag, strict mode, five approval gates, no persistent database, trace/debug events, bounded controls, fallback travel adapters, itinerary generation, review scoring, calendar export, tests, and deployment docs.
- Live adapter coverage: SerpAPI, Tavily, Google Places, and Google Maps adapters include concrete live API calls behind the same fallback policy. Integration tests remain skippable without credentials.
- Placeholder scan: This plan does not include `TBD`, `TODO`, unnamed future files, or intentionally incomplete adapter bodies.
- Type consistency: `TravelState`, `WorkflowState`, `TraceLogger`, `Settings`, approval keys, and function names are defined before later tasks reference them.
