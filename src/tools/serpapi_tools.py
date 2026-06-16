from __future__ import annotations

from datetime import date, datetime, timedelta

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
                **_hotel_date_params(query),
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
    _raise_for_serpapi_error(response, params["engine"])
    data = response.json()
    if params["engine"] == "google_flights":
        return data.get("best_flights") or data.get("other_flights") or []
    return data.get("properties") or []


def _raise_for_serpapi_error(response: requests.Response, engine: str) -> None:
    status_code = getattr(response, "status_code", None)
    if status_code is not None and status_code < 400:
        return
    detail = _serpapi_error_detail(response)
    if status_code is not None and status_code >= 400:
        raise RuntimeError(f"SerpAPI {engine} returned HTTP {status_code}. {detail}".strip())
    response.raise_for_status()


def _serpapi_error_detail(response: requests.Response) -> str:
    try:
        payload = response.json()
    except (AttributeError, ValueError):
        payload = {}
    detail = payload.get("error") or payload.get("message") or getattr(response, "text", "")
    return str(detail).strip()


def _hotel_date_params(query: dict) -> dict[str, str]:
    check_in = _parse_iso_date(query.get("start_date"))
    if not check_in:
        raise RuntimeError("SerpAPI Hotels requires a valid start_date for check_in_date")
    days = _coerce_positive_int(query.get("days"), default=1)
    check_out = check_in + timedelta(days=days)
    return {
        "check_in_date": check_in.isoformat(),
        "check_out_date": check_out.isoformat(),
    }


def _parse_iso_date(value: object) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def _coerce_positive_int(value: object, *, default: int) -> int:
    try:
        coerced = int(float(str(value)))
    except (TypeError, ValueError):
        return default
    return max(1, coerced)
