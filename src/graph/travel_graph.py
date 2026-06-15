from src.agents.approval_agent import approve
from src.config.settings import Settings
from src.graph import nodes
from src.state.travel_state import TravelState, WorkflowState
from src.tools.policy import ToolExecutionError


def run_demo_flow_until_calendar_ready(state: TravelState, settings: Settings) -> TravelState:
    nodes.collect_preferences(state)
    if state.current_state != WorkflowState.AWAITING_PREFERENCE_APPROVAL:
        return state

    approve(state, "preference_confirmation")
    try:
        nodes.research_options(state, settings)
    except ToolExecutionError:
        return state
    if state.current_state != WorkflowState.AWAITING_DESTINATION_APPROVAL:
        return state

    approve(state, "destination_city_split")
    nodes.build_itinerary(state)
    nodes.review_plan(state)
    if state.current_state == WorkflowState.AWAITING_HIGH_RISK_DAY_APPROVAL:
        approve(state, "high_risk_day")
        state.current_state = WorkflowState.AWAITING_ITINERARY_APPROVAL

    if state.current_state != WorkflowState.AWAITING_ITINERARY_APPROVAL:
        return state

    approve(state, "final_itinerary")
    state.current_state = WorkflowState.AWAITING_CALENDAR_APPROVAL
    return state
