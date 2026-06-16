from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.schemas import ApprovalRequest, ChatRequest, ChatResponse, SessionResponse
from backend.app.session_store import SessionNotFoundError, SessionStore
from src.agents.approval_agent import approve
from src.agents.chat_intake_agent import ingest_user_message
from src.config.settings import Settings
from src.exports.itinerary_export import itinerary_to_markdown, trace_to_json_bytes
from src.graph import nodes
from src.observability.trace_logger import TraceLogger
from src.state.travel_state import TravelState, WorkflowState
from src.tools.calendar_tools import CalendarExportError, generate_ics
from src.tools.policy import ToolExecutionError


app = FastAPI(title="Travel Concierge Agent API", version="0.1.0")
store = SessionStore()

frontend_origin = os.environ.get("FRONTEND_ORIGIN", "").strip()
allowed_origins = [
    origin
    for origin in [
        frontend_origin,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    if origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _settings() -> Settings:
    return Settings.from_env()


def _snapshot(session_id: str, state: TravelState, chat_history: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "state": state.to_dict(),
        "chat_history": chat_history,
    }


def _get_session_or_404(session_id: str) -> tuple[TravelState, list[dict[str, str]]]:
    try:
        return store.get(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc


def reset_for_new_trip(state: TravelState, user_input: dict[str, Any]) -> None:
    state.user_input = user_input
    state.preferences = {}
    state.destination_plan = {}
    state.flights = []
    state.hotels = []
    state.attractions = []
    state.restaurants = []
    state.transit_estimates = []
    state.itinerary = []
    state.review = {}
    state.approvals = {}
    state.current_state = WorkflowState.COLLECTING_REQUIREMENTS
    state.tool_call_count = 0
    state.token_count = 0
    state.review_iteration_count = 0
    state.planner_iteration_count = 0
    state.trace_events = []
    state.errors = []
    state.generated_ics = None


def reset_planning_outputs(state: TravelState) -> None:
    reset_for_new_trip(state, {})


def run_preference_step(state: TravelState) -> None:
    nodes.collect_preferences(state)


def generate_calendar(state: TravelState) -> None:
    state.current_state = WorkflowState.GENERATING_CALENDAR
    try:
        state.generated_ics = generate_ics(state.itinerary)
    except CalendarExportError as exc:
        state.generated_ics = None
        state.current_state = WorkflowState.FAILED
        state.errors.append(str(exc))
        TraceLogger(state).log(
            node="Calendar Export",
            event_type="export_failed",
            action="generate_ics",
            input_summary="Approved itinerary",
            output_summary="Calendar export failed",
            status="error",
            error=str(exc),
        )
        return
    state.current_state = WorkflowState.COMPLETE


def advance_approval_gate(state: TravelState, settings: Settings, gate: str) -> None:
    approve(state, gate)
    try:
        if gate == "preference_confirmation":
            nodes.research_options(state, settings)
        elif gate == "destination_city_split":
            nodes.build_itinerary(state)
            nodes.review_plan(state)
            if state.current_state == WorkflowState.AWAITING_ITINERARY_APPROVAL:
                state.current_state = WorkflowState.AWAITING_HIGH_RISK_DAY_APPROVAL
        elif gate == "high_risk_day":
            state.current_state = WorkflowState.AWAITING_ITINERARY_APPROVAL
        elif gate == "final_itinerary":
            state.current_state = WorkflowState.AWAITING_CALENDAR_APPROVAL
        elif gate == "calendar_creation":
            generate_calendar(state)
    except ToolExecutionError as exc:
        state.errors.append(str(exc))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/sessions", response_model=SessionResponse)
def create_session() -> dict[str, Any]:
    session_id, state, chat_history = store.create()
    return _snapshot(session_id, state, chat_history)


@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str) -> dict[str, Any]:
    state, chat_history = _get_session_or_404(session_id)
    return _snapshot(session_id, state, chat_history)


@app.post("/api/sessions/{session_id}/chat", response_model=ChatResponse)
def chat(session_id: str, request: ChatRequest) -> dict[str, Any]:
    state, chat_history = _get_session_or_404(session_id)
    settings = _settings()
    message = request.message.strip()
    if state.current_state != WorkflowState.COLLECTING_REQUIREMENTS:
        reset_planning_outputs(state)
    chat_history.append({"role": "user", "content": message})
    preferences, reply, ready = ingest_user_message(state.user_input, message, settings=settings)
    state.user_input = preferences
    chat_history.append({"role": "assistant", "content": reply})
    if ready:
        reset_for_new_trip(state, preferences)
        run_preference_step(state)
    store.save(session_id)
    return {
        **_snapshot(session_id, state, chat_history),
        "reply": reply,
        "ready": ready,
    }


@app.post("/api/sessions/{session_id}/approve", response_model=SessionResponse)
def approve_gate(session_id: str, request: ApprovalRequest) -> dict[str, Any]:
    state, chat_history = _get_session_or_404(session_id)
    advance_approval_gate(state, _settings(), request.gate)
    store.save(session_id)
    return _snapshot(session_id, state, chat_history)


@app.get("/api/sessions/{session_id}/exports/itinerary.md")
def export_itinerary(session_id: str) -> Response:
    state, _chat_history = _get_session_or_404(session_id)
    if not state.itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not available")
    return Response(
        itinerary_to_markdown(state.itinerary),
        media_type="text/markdown",
        headers={"Content-Disposition": 'attachment; filename="travel-itinerary.md"'},
    )


@app.get("/api/sessions/{session_id}/exports/calendar.ics")
def export_calendar(session_id: str) -> Response:
    state, _chat_history = _get_session_or_404(session_id)
    if not state.generated_ics:
        raise HTTPException(status_code=404, detail="Calendar not available")
    return Response(
        state.generated_ics,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="travel-itinerary.ics"'},
    )


@app.get("/api/sessions/{session_id}/exports/trace.json")
def export_trace(session_id: str) -> Response:
    state, _chat_history = _get_session_or_404(session_id)
    return Response(
        trace_to_json_bytes(state),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="travel-trace.json"'},
    )

