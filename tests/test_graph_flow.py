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
