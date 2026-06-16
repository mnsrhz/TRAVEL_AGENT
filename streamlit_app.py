from __future__ import annotations

import os

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from src.agents.approval_agent import approve
from src.config.settings import Settings
from src.exports.itinerary_export import itinerary_to_markdown, trace_to_json_bytes
from src.graph.travel_graph import run_demo_flow_until_calendar_ready
from src.state.travel_state import TravelState, WorkflowState
from src.tools.calendar_tools import generate_ics
from src.ui.components import (
    render_approval_panel,
    render_itinerary,
    render_preferences,
    render_status,
    render_trace_panel,
    render_workflow_sidebar,
)
from src.ui.styles import APP_CSS


st.set_page_config(page_title="Travel Concierge Agent", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)


def get_state() -> TravelState:
    if "travel_state" not in st.session_state:
        st.session_state.travel_state = TravelState()
    return st.session_state.travel_state


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


settings = Settings.from_sources(os.environ, get_streamlit_secrets())
state = get_state()

left, center, right = st.columns([0.22, 0.52, 0.26], gap="small")

with left:
    render_workflow_sidebar(state, settings)

with center:
    st.markdown(f"### {trip_heading(state)}")
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

    render_status(state)

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
