import requests

from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools import fallback_data
from src.tools.policy import run_tool_with_policy


def search_flights(state: TravelState, settings: Settings, query: dict) -> list[dict]:
    return run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="SerpAPI Flights",
        required_key="SERPAPI_API_KEY",
        live_call=lambda: _serpapi_search(
            settings,
            {
                "engine": "google_flights",
                "departure_id": query.get("origin"),
                "arrival_id": query.get("destination"),
                "outbound_date": query.get("start_date"),
                "currency": "USD",
            },
        ),
        fallback_call=lambda: fallback_data.DEMO_FLIGHTS,
        input_summary=f"{query.get('origin')} to {query.get('destination')}",
    )


def search_hotels(state: TravelState, settings: Settings, query: dict) -> list[dict]:
    return run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="SerpAPI Hotels",
        required_key="SERPAPI_API_KEY",
        live_call=lambda: _serpapi_search(
            settings,
            {
                "engine": "google_hotels",
                "q": f"hotels in {query.get('destination')}",
                "currency": "USD",
            },
        ),
        fallback_call=lambda: fallback_data.DEMO_HOTELS,
        input_summary=f"Hotels in {query.get('destination')}",
    )


def _serpapi_search(settings: Settings, params: dict) -> list[dict]:
    response = requests.get(
        "https://serpapi.com/search.json",
        params={**params, "api_key": settings.serpapi_api_key},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if params["engine"] == "google_flights":
        return data.get("best_flights") or data.get("other_flights") or []
    return data.get("properties") or []
