from __future__ import annotations

import requests

from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools import fallback_data
from src.tools.policy import run_tool_with_policy


PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_FIELD_MASK = "places.id,places.displayName,places.formattedAddress,places.rating"


def search_restaurants(state: TravelState, settings: Settings, query: dict) -> list[dict]:
    return run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="Google Places Restaurants",
        required_key="GOOGLE_MAPS_API_KEY",
        live_call=lambda: _search_places(settings, query),
        fallback_call=lambda: fallback_data.DEMO_RESTAURANTS,
        input_summary=f"{query.get('dietary')} restaurants in {query.get('city')}",
    )


def _search_places(settings: Settings, query: dict) -> list[dict]:
    text = f"{query.get('dietary', '')} restaurants in {query.get('city')}"
    response = requests.post(
        PLACES_TEXT_SEARCH_URL,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": settings.google_maps_api_key or "",
            "X-Goog-FieldMask": PLACES_FIELD_MASK,
        },
        json={"textQuery": text, "includedType": "restaurant", "pageSize": 8},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    return [
        {
            "name": item.get("displayName", {}).get("text"),
            "city": query.get("city"),
            "rating": item.get("rating"),
            "address": item.get("formattedAddress"),
            "place_id": item.get("id"),
            "source": "google_places_new",
        }
        for item in payload.get("places", [])[:8]
    ]
