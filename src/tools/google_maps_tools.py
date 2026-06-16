from __future__ import annotations

import re

import requests

from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools import fallback_data
from src.tools.policy import run_tool_with_policy


ROUTES_MATRIX_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
ROUTES_FIELD_MASK = "originIndex,destinationIndex,status,condition,distanceMeters,duration"


def estimate_transit(state: TravelState, settings: Settings, query: dict) -> list[dict]:
    return run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="Google Maps Transit",
        required_key="GOOGLE_MAPS_API_KEY",
        live_call=lambda: _estimate_google_transit(settings, query),
        fallback_call=lambda: fallback_data.DEMO_TRANSIT,
        input_summary=f"{query.get('origin')} to {query.get('destination')}",
    )


def _estimate_google_transit(settings: Settings, query: dict) -> list[dict]:
    payload = {
        "origins": [{"waypoint": {"address": query.get("origin")}}],
        "destinations": [{"waypoint": {"address": query.get("destination")}}],
        "travelMode": _routes_travel_mode(query.get("mode", "transit")),
    }
    response = requests.post(
        ROUTES_MATRIX_URL,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": settings.google_maps_api_key or "",
            "X-Goog-FieldMask": ROUTES_FIELD_MASK,
        },
        json=payload,
        timeout=20,
    )
    _raise_for_routes_http_error(response)
    return [_extract_distance_matrix_result(response.json(), query)]


def _extract_distance_matrix_result(response: dict | list, query: dict) -> dict:
    element = _first_route_matrix_element(response)
    status = element.get("status", {})
    if isinstance(status, dict) and status.get("code"):
        raise RuntimeError(f"Google Routes returned {status.get('message') or status.get('code')}")
    if element.get("condition") and element.get("condition") != "ROUTE_EXISTS":
        raise RuntimeError(f"Google Routes returned {element.get('condition')}")
    duration_seconds = _parse_duration_seconds(element.get("duration"))
    if duration_seconds is None:
        raise RuntimeError("Google Maps response missing route duration")
    return {
        "origin": query.get("origin"),
        "destination": query.get("destination"),
        "duration_minutes": round(duration_seconds / 60),
        "distance": _format_distance(element.get("distanceMeters")),
        "mode": query.get("mode", "transit"),
        "source": "google_routes",
    }


def _first_route_matrix_element(response: dict | list) -> dict:
    if isinstance(response, list):
        if not response:
            raise RuntimeError("Google Maps response missing route element")
        return response[0]
    try:
        return response["rows"][0]["elements"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Google Maps response missing route element") from exc


def _parse_duration_seconds(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("value")
    if isinstance(value, (int, float)):
        return float(value)
    match = re.fullmatch(r"(\d+(?:\.\d+)?)s", str(value))
    return float(match.group(1)) if match else None


def _format_distance(distance_meters: object) -> str | None:
    if distance_meters is None:
        return None
    try:
        meters = float(distance_meters)
    except (TypeError, ValueError):
        return None
    if meters >= 1000:
        return f"{meters / 1000:.1f} km"
    return f"{round(meters)} m"


def _routes_travel_mode(mode: object) -> str:
    return {
        "driving": "DRIVE",
        "drive": "DRIVE",
        "walking": "WALK",
        "walk": "WALK",
        "bicycling": "BICYCLE",
        "bike": "BICYCLE",
        "transit": "TRANSIT",
    }.get(str(mode or "transit").lower(), "TRANSIT")


def _raise_for_routes_http_error(response: requests.Response) -> None:
    status_code = getattr(response, "status_code", None)
    if status_code is not None and status_code < 400:
        return

    details = _google_error_details(response)
    if status_code == 403:
        raise RuntimeError(
            "Google Routes API permission denied. In Google Cloud, enable the Routes API for this project, "
            "confirm billing is active, and make sure GOOGLE_MAPS_API_KEY is allowed to call routes.googleapis.com. "
            f"{details}"
        )
    if status_code is not None and status_code >= 400:
        raise RuntimeError(f"Google Routes API returned HTTP {status_code}. {details}")

    response.raise_for_status()


def _google_error_details(response: requests.Response) -> str:
    try:
        error = response.json().get("error", {})
    except (AttributeError, ValueError):
        error = {}
    status = error.get("status")
    message = error.get("message") or getattr(response, "text", "")
    parts = []
    if status:
        parts.append(f"Google status: {status}.")
    if message:
        parts.append(f"Google message: {message}")
    return " ".join(parts).strip()
