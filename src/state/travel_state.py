from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        pass
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
