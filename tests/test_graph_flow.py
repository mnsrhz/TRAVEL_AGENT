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


def test_graph_pauses_when_required_input_missing():
    state = TravelState(user_input={"destination": "Japan"})
    settings = Settings(None, None, None, None, allow_demo_fallbacks=True)

    result = run_demo_flow_until_calendar_ready(state, settings)

    assert result.current_state == WorkflowState.COLLECTING_REQUIREMENTS
    assert not result.approvals
    assert "Missing fields" in result.trace_events[-1].output_summary


def test_graph_stops_on_strict_tool_failure():
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
    settings = Settings(None, None, None, None, allow_demo_fallbacks=False)

    result = run_demo_flow_until_calendar_ready(state, settings)

    assert result.current_state == WorkflowState.FAILED
    assert "Missing SERPAPI_API_KEY" in result.errors[-1]


def test_graph_does_not_force_calendar_approval_when_review_requires_rebuild(monkeypatch):
    from src.graph import nodes

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

    def low_score_review(current_state):
        current_state.current_state = WorkflowState.BUILDING_ITINERARY
        current_state.review = {"score": 7.0, "findings": ["Needs revision"], "requires_high_risk_approval": False}
        return current_state

    monkeypatch.setattr(nodes, "review_plan", low_score_review)

    result = run_demo_flow_until_calendar_ready(state, settings)

    assert result.current_state == WorkflowState.BUILDING_ITINERARY
    assert result.approvals.get("final_itinerary") is not True
