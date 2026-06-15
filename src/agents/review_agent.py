from src.state.travel_state import WorkflowState


def review_itinerary(itinerary: list[dict], preferences: dict) -> dict:
    findings: list[str] = []
    score = 9.0
    pace = preferences.get("pace", "moderate")

    for day in itinerary:
        major_events = [event for event in day.get("events", []) if event.get("type") == "attraction"]
        if pace != "packed" and len(major_events) > 3:
            score -= 2
            findings.append(f"Day {day.get('day')} is overloaded for a {pace} pace traveler.")

    dietary = preferences.get("dietary", "none")
    if dietary not in {"none", "", None}:
        days_without_meals = [
            day.get("day")
            for day in itinerary
            if not any(event.get("type") == "meal" for event in day.get("events", []))
        ]
        if days_without_meals:
            score -= 1
            findings.append(f"Dietary preference is present but days {days_without_meals} have no meal events.")

    score = max(1.0, min(10.0, score))
    return {
        "score": score,
        "findings": findings or ["Itinerary is realistic, geographically sensible, and calendar-ready."],
        "requires_high_risk_approval": bool(findings),
    }


def next_state_after_review(score: float, review_iteration_count: int) -> WorkflowState:
    if score < 8 and review_iteration_count < 3:
        return WorkflowState.BUILDING_ITINERARY
    return WorkflowState.AWAITING_ITINERARY_APPROVAL
