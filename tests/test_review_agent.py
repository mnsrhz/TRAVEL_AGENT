from src.agents.itinerary_agent import build_demo_itinerary
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
