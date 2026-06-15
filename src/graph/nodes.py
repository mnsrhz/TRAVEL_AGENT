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
