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
    day_count = max(1, int(preferences.get("days", 10)))
    destination = str(preferences.get("destination", "Japan")).lower()
    city_by_day = _city_sequence(day_count, destination)
    highlights = {
        "Tokyo": ["Senso-ji Temple", "Shibuya Crossing", "Harajuku walk"],
        "Kyoto": ["Fushimi Inari Taisha", "Gion district", "Kiyomizu-dera"],
        "Osaka": ["Dotonbori", "Osaka Castle", "Kuromon Market"],
    }
    itinerary = []
    for index, city in enumerate(city_by_day):
        day = start_date + timedelta(days=index)
        names = highlights.get(
            city,
            [
                f"{city} landmark walk",
                f"{city} local market",
                f"{city} cultural district",
            ],
        )
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


def _city_sequence(day_count: int, destination: str) -> list[str]:
    if "japan" not in destination:
        return [destination.title() or "Destination"] * day_count
    template = ["Tokyo", "Tokyo", "Tokyo", "Tokyo", "Kyoto", "Kyoto", "Kyoto", "Osaka", "Osaka", "Osaka"]
    if day_count <= len(template):
        return template[:day_count]
    return template + ["Osaka"] * (day_count - len(template))
