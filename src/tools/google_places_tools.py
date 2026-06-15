from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools import fallback_data
from src.tools.policy import run_tool_with_policy


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
    import googlemaps

    client = googlemaps.Client(key=settings.google_maps_api_key)
    text = f"{query.get('dietary', '')} restaurants in {query.get('city')}"
    response = client.places(query=text, type="restaurant")
    return [
        {
            "name": item.get("name"),
            "city": query.get("city"),
            "rating": item.get("rating"),
            "address": item.get("formatted_address"),
            "place_id": item.get("place_id"),
            "source": "google_places",
        }
        for item in response.get("results", [])[:8]
    ]
