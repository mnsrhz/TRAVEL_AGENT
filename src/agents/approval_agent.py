from src.state.travel_state import TravelState


APPROVAL_GATES = (
    "preference_confirmation",
    "destination_city_split",
    "high_risk_day",
    "final_itinerary",
    "calendar_creation",
)


def approve(state: TravelState, gate: str) -> None:
    if gate not in APPROVAL_GATES:
        raise ValueError(f"Unknown approval gate: {gate}")
    state.approvals[gate] = True


def is_approved(state: TravelState, gate: str) -> bool:
    return state.approvals.get(gate) is True
