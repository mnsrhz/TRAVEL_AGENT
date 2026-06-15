from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from icalendar import Calendar, Event


class CalendarExportError(ValueError):
    pass


def _parse_dt(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CalendarExportError(f"Invalid event datetime: {value}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def generate_ics(itinerary: list[dict]) -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//Travel Concierge Agent//streamlit//")
    calendar.add("version", "2.0")

    for day in itinerary:
        for item in day.get("events", []):
            _require_fields(item, ("title", "start", "end"))
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


def _require_fields(item: dict, fields: tuple[str, ...]) -> None:
    for field in fields:
        if not item.get(field):
            raise CalendarExportError(f"Missing required event field: {field}")
