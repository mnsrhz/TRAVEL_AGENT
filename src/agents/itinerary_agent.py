from __future__ import annotations

from datetime import datetime, timedelta


def _event(day: datetime, start_hour: int, duration_hours: float, title: str, location: str, event_type: str) -> dict:
    start = day.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=int(duration_hours * 60))
    return {
        "type": event_type,
        "title": title,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "location": location,
        "description": "Calendar-ready recommendation with estimated timing, rationale, and fallback option.",
        "cost": "$0-$80",
        "source": "demo",
    }


def build_demo_itinerary(preferences: dict) -> list[dict]:
    start_date = datetime.fromisoformat(preferences.get("start_date", "2026-10-10"))
    city_by_day = ["Tokyo"] * 4 + ["Kyoto"] * 3 + ["Osaka"] * 3
    highlights = {
        "Tokyo": ["Senso-ji Temple", "Shibuya Crossing", "Harajuku walk"],
        "Kyoto": ["Fushimi Inari Taisha", "Gion district", "Kiyomizu-dera"],
        "Osaka": ["Dotonbori", "Osaka Castle", "Kuromon Market"],
    }
    itinerary = []
    for index, city in enumerate(city_by_day):
        day = start_date + timedelta(days=index)
        names = highlights[city]
        itinerary.append(
            {
                "day": index + 1,
                "date": day.date().isoformat(),
                "city": city,
                "events": [
                    _event(day, 9, 2, names[index % len(names)], city, "attraction"),
                    _event(day, 12, 1, f"Vegetarian lunch in {city}", city, "meal"),
                    _event(day, 14, 2, f"{city} neighborhood exploration", city, "attraction"),
                ],
            }
        )
    return itinerary
