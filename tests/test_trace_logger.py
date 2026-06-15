from src.observability.trace_logger import TraceLogger
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
