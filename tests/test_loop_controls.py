from src.agents.review_agent import next_state_after_review
from src.state.travel_state import WorkflowState


def test_low_score_under_limit_returns_to_builder():
    assert next_state_after_review(score=7.0, review_iteration_count=1) == WorkflowState.BUILDING_ITINERARY


def test_low_score_at_limit_goes_to_approval_with_explanation():
    assert next_state_after_review(score=7.0, review_iteration_count=3) == WorkflowState.AWAITING_ITINERARY_APPROVAL


def test_passing_score_goes_to_approval():
    assert next_state_after_review(score=8.5, review_iteration_count=1) == WorkflowState.AWAITING_ITINERARY_APPROVAL
