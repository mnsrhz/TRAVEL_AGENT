from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from icalendar import Calendar, Event


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def generate_ics(itinerary: list[dict]) -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//Travel Concierge Agent//streamlit//")
    calendar.add("version", "2.0")

    for day in itinerary:
        for item in day.get("events", []):
            event = Event()
            event.add("uid", f"{uuid4()}@travel-concierge")
            event.add("summary", item["title"])
            event.add("dtstart", _parse_dt(item["start"]))
            event.add("dtend", _parse_dt(item["end"]))
            event.add("location", item.get("location", ""))
            description = item.get("description", "")
            cost = item.get("cost")
            source = item.get("source")
            notes = [description]
            if cost:
                notes.append(f"Estimated cost: {cost}")
            if source:
                notes.append(f"Source: {source}")
            event.add("description", "\n".join(part for part in notes if part))
            calendar.add_component(event)

    return calendar.to_ical()
