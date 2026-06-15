from __future__ import annotations

import json
import re

from src.state.travel_state import TravelState


def itinerary_to_markdown(itinerary: list[dict]) -> str:
    lines = ["# Travel Itinerary", ""]
    for day in itinerary:
        lines.append(f"## Day {day.get('day', '?')} - {_escape_markdown(day.get('date', 'unscheduled'))}")
        for event in day.get("events", []):
            title = _escape_markdown(event.get("title", "Untitled event"))
            start = _escape_markdown(event.get("start", "unknown start"))
            end = _escape_markdown(event.get("end", "unknown end"))
            lines.append(f"- **{title}** ({start} to {end})")
            if event.get("location"):
                lines.append(f"  - Location: {_escape_markdown(event['location'])}")
            if event.get("description"):
                lines.append(f"  - Notes: {_escape_markdown(event['description'])}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def trace_to_json_bytes(state: TravelState) -> bytes:
    return json.dumps(
        [event.to_dict() for event in state.trace_events],
        indent=2,
        default=str,
    ).encode("utf-8")


def _escape_markdown(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text.translate(str.maketrans({char: f"\\{char}" for char in r"\`*[]"}))
