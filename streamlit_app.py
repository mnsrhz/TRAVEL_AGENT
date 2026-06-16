from __future__ import annotations

import os

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from src.agents.approval_agent import approve
from src.agents.chat_intake_agent import ingest_user_message
from src.config.settings import Settings
from src.exports.itinerary_export import itinerary_to_markdown, trace_to_json_bytes
from src.graph import nodes
from src.observability.trace_logger import TraceLogger
from src.state.travel_state import TravelState, WorkflowState
from src.tools.calendar_tools import CalendarExportError, generate_ics
from src.tools.policy import ToolExecutionError
from src.ui.components import (
    render_bottom_chat_hint,
    render_approval_panel,
    render_destination_plan,
    render_itinerary,
    render_main_content_end,
    render_main_content_start,
    render_preferences,
    render_review_summary,
    render_shell_marker,
    render_status,
    render_topbar,
    render_tool_readiness,
    render_trace_panel,
    render_workflow_sidebar,
)
from src.ui.styles import APP_CSS


st.set_page_config(page_title="Travel Concierge Agent", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)
render_shell_marker()


def get_state() -> TravelState:
    if "travel_state" not in st.session_state:
        st.session_state.travel_state = TravelState()
    return st.session_state.travel_state


def get_chat_history() -> list[dict[str, str]]:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": "Tell me about the trip you want in plain English. I will ask for anything missing.",
            }
        ]
    return st.session_state.chat_history


def get_streamlit_secrets() -> dict[str, object]:
    try:
        return dict(st.secrets)
    except StreamlitSecretNotFoundError:
        return {}


def trip_heading(state: TravelState) -> str:
    trip = state.preferences or state.user_input
    destination = trip.get("destination", "Japan")
    days = trip.get("days", 10)
    return f"{days}-day {destination} travel plan"


def reset_for_new_trip(state: TravelState, user_input: dict) -> None:
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
    state.user_input = {}
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


def handle_chat_message(state: TravelState, settings: Settings, message: str) -> None:
    history = get_chat_history()
    history.append({"role": "user", "content": message})
    if state.current_state != WorkflowState.COLLECTING_REQUIREMENTS:
        reset_planning_outputs(state)
    preferences, reply, ready = ingest_user_message(state.user_input, message, settings=settings)
    state.user_input = preferences
    history.append({"role": "assistant", "content": reply})
    if ready:
        reset_for_new_trip(state, preferences)
        run_preference_step(state)


def run_preference_step(state: TravelState) -> None:
    nodes.collect_preferences(state)


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


APPROVAL_RENDER_CONFIG = {
    WorkflowState.AWAITING_PREFERENCE_APPROVAL: (
        "preference_confirmation",
        "Approval gate 1 of 5 - Preference confirmation",
        "Approve the normalized trip preferences before live research begins.",
        "Approve preferences and research",
    ),
    WorkflowState.AWAITING_DESTINATION_APPROVAL: (
        "destination_city_split",
        "Approval gate 2 of 5 - Destination split",
        "Approve the city split and research summary before building the itinerary.",
        "Approve destination split",
    ),
    WorkflowState.AWAITING_HIGH_RISK_DAY_APPROVAL: (
        "high_risk_day",
        "Approval gate 3 of 5 - Safety review",
        "Review the itinerary quality findings before continuing.",
        "Approve safety review",
    ),
    WorkflowState.AWAITING_ITINERARY_APPROVAL: (
        "final_itinerary",
        "Approval gate 4 of 5 - Final itinerary",
        "Approve the day-by-day plan before calendar creation is enabled.",
        "Approve final itinerary",
    ),
    WorkflowState.AWAITING_CALENDAR_APPROVAL: (
        "calendar_creation",
        "Approval gate 5 of 5 - Calendar creation",
        "Approve calendar creation to generate the ICS file.",
        "Approve calendar and generate ICS",
    ),
}


def render_current_approval(state: TravelState, settings: Settings) -> None:
    config = APPROVAL_RENDER_CONFIG.get(state.current_state)
    if not config:
        return
    gate, title, body, button_label = config
    render_approval_panel(title, body)
    if st.button(button_label, type="primary", key=f"approve_{gate}"):
        advance_approval_gate(state, settings, gate)
        st.rerun()


settings = Settings.from_sources(os.environ, get_streamlit_secrets())
state = get_state()
chat_history = get_chat_history()
prompt = st.chat_input("Tell me what kind of trip you want", key="trip_chat_input")
if prompt:
    handle_chat_message(state, settings, prompt)

left, center, right = st.columns([0.22, 0.52, 0.26], gap="small")

with left:
    render_workflow_sidebar(state, settings)
    render_tool_readiness(settings)

with center:
    render_topbar(state, settings)
    render_main_content_start()
    for message in chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    render_status(state)

    if state.preferences or state.user_input:
        render_preferences(state)

    render_destination_plan(state)

    if state.itinerary:
        render_itinerary(state)
        render_review_summary(state)

    render_current_approval(state, settings)

    if state.itinerary:
        st.download_button("Download itinerary markdown", itinerary_to_markdown(state.itinerary), file_name="travel-itinerary.md")
    if state.generated_ics:
        st.download_button("Download calendar ICS", state.generated_ics, file_name="travel-itinerary.ics")
    if state.trace_events:
        st.download_button("Download trace JSON", trace_to_json_bytes(state), file_name="travel-trace.json")
    render_bottom_chat_hint()
    render_main_content_end()

with right:
    render_trace_panel(state)
