from __future__ import annotations

import json

from src.state.travel_state import TravelState


def itinerary_to_markdown(itinerary: list[dict]) -> str:
    lines = ["# Travel Itinerary", ""]
    for day in itinerary:
        lines.append(f"## Day {day['day']} - {day['date']}")
        for event in day.get("events", []):
            lines.append(f"- **{event['title']}** ({event['start']} to {event['end']})")
            if event.get("location"):
                lines.append(f"  - Location: {event['location']}")
            if event.get("description"):
                lines.append(f"  - Notes: {event['description']}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def trace_to_json_bytes(state: TravelState) -> bytes:
    return json.dumps([event.to_dict() for event in state.trace_events], indent=2).encode("utf-8")
