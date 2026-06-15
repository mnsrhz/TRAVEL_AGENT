from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools import fallback_data
from src.tools.policy import run_tool_with_policy


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
    import googlemaps

    client = googlemaps.Client(key=settings.google_maps_api_key)
    response = client.distance_matrix(
        origins=[query.get("origin")],
        destinations=[query.get("destination")],
        mode=query.get("mode", "transit"),
    )
    return [_extract_distance_matrix_result(response, query)]


def _extract_distance_matrix_result(response: dict, query: dict) -> dict:
    try:
        element = response["rows"][0]["elements"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Google Maps response missing route element") from exc
    if element.get("status") != "OK":
        raise RuntimeError(f"Google Maps returned {element.get('status')}")
    duration = element.get("duration", {}).get("value")
    if duration is None:
        raise RuntimeError("Google Maps response missing route duration")
    return {
        "origin": query.get("origin"),
        "destination": query.get("destination"),
        "duration_minutes": round(duration / 60),
        "distance": element.get("distance", {}).get("text"),
        "mode": query.get("mode", "transit"),
        "source": "google_maps",
    }
