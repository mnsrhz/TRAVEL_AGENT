import pytest

from src.agents.approval_agent import approve, is_approved
from src.state.travel_state import TravelState


def test_is_approved_rejects_unknown_gate():
    with pytest.raises(ValueError, match="Unknown approval gate"):
        is_approved(TravelState(), "typo_gate")


def test_approve_records_known_gate():
    state = TravelState()
    approve(state, "calendar_creation")
    assert is_approved(state, "calendar_creation") is True
