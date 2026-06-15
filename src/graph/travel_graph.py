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
