from src.agents.itinerary_agent import build_demo_itinerary
from src.agents.preference_agent import normalize_preferences
from src.agents.review_agent import review_itinerary


def test_review_flags_overloaded_moderate_day():
    itinerary = [
        {
            "day": 1,
            "date": "2026-10-10",
            "events": [
                {"type": "attraction", "title": "A", "start": "2026-10-10T09:00:00", "end": "2026-10-10T10:00:00"},
                {"type": "attraction", "title": "B", "start": "2026-10-10T11:00:00", "end": "2026-10-10T12:00:00"},
                {"type": "attraction", "title": "C", "start": "2026-10-10T13:00:00", "end": "2026-10-10T14:00:00"},
                {"type": "attraction", "title": "D", "start": "2026-10-10T15:00:00", "end": "2026-10-10T16:00:00"},
            ],
        }
    ]
    review = review_itinerary(itinerary, {"pace": "moderate", "dietary": "vegetarian"})
    assert review["score"] < 8
    assert review["requires_high_risk_approval"] is True
    assert "overloaded" in review["findings"][0].lower()


def test_demo_itinerary_has_calendar_ready_events():
    itinerary = build_demo_itinerary({"start_date": "2026-10-10", "dietary": "vegetarian"})
    assert len(itinerary) == 10
    first_event = itinerary[0]["events"][0]
    assert {"title", "start", "end", "location", "description"}.issubset(first_event)


def test_demo_itinerary_respects_requested_day_count():
    itinerary = build_demo_itinerary({"start_date": "2026-10-10", "days": 5, "destination": "Japan"})
    assert len(itinerary) == 5


def test_normalize_preferences_handles_real_world_number_strings():
    preferences = normalize_preferences(
        {
            "destination": "Japan",
            "days": "10 days",
            "origin": "SFO",
            "start_date": "2026-10-10",
            "budget": "$1,500.00",
            "pace": None,
            "dietary": 123,
        }
    )
    assert preferences["days"] == 10
    assert preferences["budget"] == 1500
    assert preferences["pace"] == "moderate"
    assert preferences["dietary"] == "123"


def test_review_flags_missing_meals_for_dietary_trip_days():
    itinerary = [
        {"day": 1, "date": "2026-10-10", "events": [{"type": "meal", "title": "Vegetarian lunch"}]},
        {"day": 2, "date": "2026-10-11", "events": [{"type": "attraction", "title": "Temple"}]},
    ]
    review = review_itinerary(itinerary, {"pace": "moderate", "dietary": "vegetarian"})
    assert review["score"] < 9
    assert any("dietary" in finding.lower() for finding in review["findings"])
