from src.observability.trace_logger import TraceLogger
from src.observability.token_tracker import estimate_tokens, token_budget_status
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


def test_trace_logger_ignores_negative_usage_counts():
    state = TravelState()
    TraceLogger(state).log(
        node="Tool",
        event_type="tool_completed",
        action="bad_usage",
        input_summary="input",
        output_summary="output",
        status="success",
        tokens_used=-10,
        tool_calls_used=-1,
    )
    assert state.token_count == 0
    assert state.tool_call_count == 0


def test_token_tracker_handles_whitespace_and_invalid_budget():
    assert estimate_tokens("   ") == 0
    status = token_budget_status(10, budget=0)
    assert status["used"] == 10
    assert status["budget"] == 0
    assert status["ratio"] == 1.0
    assert status["should_pause"] is True


def test_travel_state_serializes_without_raw_ics_bytes():
    state = TravelState(generated_ics=b"BEGIN:VCALENDAR")
    payload = state.to_dict()
    assert payload["generated_ics"] == "<generated>"
