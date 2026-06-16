import pytest
import requests

from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools.google_maps_tools import estimate_transit
from src.tools.google_maps_tools import _extract_distance_matrix_result
from src.tools.google_maps_tools import _estimate_google_transit
from src.tools.google_places_tools import search_restaurants
from src.tools.google_places_tools import _search_places
from src.tools.policy import ToolExecutionError, run_tool_with_policy
from src.tools.serpapi_tools import search_flights, search_hotels
from src.tools.tavily_tools import search_attractions


def test_policy_uses_fallback_when_key_missing_and_flag_on():
    state = TravelState()
    settings = Settings(None, None, None, None, allow_demo_fallbacks=True)

    result = run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="Tavily",
        required_key="TAVILY_API_KEY",
        live_call=lambda: [{"name": "Live"}],
        fallback_call=lambda: [{"name": "Fallback", "source": "demo"}],
        input_summary="Kyoto attractions",
    )

    assert result == [{"name": "Fallback", "source": "demo"}]
    assert state.trace_events[-1].status == "fallback"
    assert state.trace_events[-1].tool_calls_used == 0
    assert state.tool_call_count == 0


def test_policy_raises_when_key_missing_and_strict():
    state = TravelState()
    settings = Settings(None, None, None, None, allow_demo_fallbacks=False)

    with pytest.raises(ToolExecutionError):
        run_tool_with_policy(
            state=state,
            settings=settings,
            tool_name="SerpAPI Flights",
            required_key="SERPAPI_API_KEY",
            live_call=lambda: [],
            fallback_call=lambda: [],
            input_summary="SFO to Tokyo",
        )

    assert state.current_state.value == "FAILED"
    assert "Missing SERPAPI_API_KEY" in state.errors[-1]


def test_policy_falls_back_after_live_exception_when_flag_on():
    state = TravelState()
    settings = Settings(None, "serp", None, None, allow_demo_fallbacks=True)

    result = run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="SerpAPI Hotels",
        required_key="SERPAPI_API_KEY",
        live_call=lambda: (_ for _ in ()).throw(RuntimeError("rate limited")),
        fallback_call=lambda: [{"hotel": "Demo hotel"}],
        input_summary="Tokyo hotels",
    )

    assert result == [{"hotel": "Demo hotel"}]
    assert state.trace_events[-1].status == "fallback"
    assert "rate limited" in state.trace_events[-1].error
    assert state.trace_events[-1].tool_calls_used == 1
    assert state.tool_call_count == 1


def test_policy_raises_traceable_error_when_fallback_fails():
    state = TravelState()
    settings = Settings(None, None, None, None, allow_demo_fallbacks=True)

    with pytest.raises(ToolExecutionError):
        run_tool_with_policy(
            state=state,
            settings=settings,
            tool_name="Tavily",
            required_key="TAVILY_API_KEY",
            live_call=lambda: [],
            fallback_call=lambda: (_ for _ in ()).throw(RuntimeError("bad demo data")),
            input_summary="Kyoto attractions",
        )

    assert state.current_state.value == "FAILED"
    assert state.trace_events[-1].status == "error"
    assert "bad demo data" in state.errors[-1]


def test_policy_raises_traceable_error_when_live_call_fails_in_strict_mode():
    state = TravelState()
    settings = Settings(None, "serp", None, None, allow_demo_fallbacks=False)

    with pytest.raises(ToolExecutionError):
        run_tool_with_policy(
            state=state,
            settings=settings,
            tool_name="SerpAPI Hotels",
            required_key="SERPAPI_API_KEY",
            live_call=lambda: (_ for _ in ()).throw(RuntimeError("quota exceeded")),
            fallback_call=lambda: [{"hotel": "Demo hotel"}],
            input_summary="Tokyo hotels",
        )

    assert state.current_state.value == "FAILED"
    assert state.trace_events[-1].status == "error"
    assert state.trace_events[-1].tool_calls_used == 1
    assert "quota exceeded" in state.errors[-1]


def test_tool_adapters_return_fallback_data_when_enabled():
    settings = Settings(None, None, None, None, allow_demo_fallbacks=True)
    state = TravelState()
    flights = search_flights(state, settings, {"origin": "SFO", "destination": "Tokyo"})
    hotels = search_hotels(state, settings, {"destination": "Tokyo"})
    attractions = search_attractions(state, settings, {"destination": "Japan"})
    restaurants = search_restaurants(state, settings, {"city": "Tokyo", "dietary": "vegetarian"})
    transit = estimate_transit(state, settings, {"origin": "Shinjuku", "destination": "Asakusa"})

    assert {"title", "source"}.issubset(flights[0])
    assert {"name", "nightly_price", "source"}.issubset(hotels[0])
    assert {"name", "duration_hours", "source"}.issubset(attractions[0])
    assert {"name", "dietary", "source"}.issubset(restaurants[0])
    assert {"origin", "destination", "duration_minutes", "source"}.issubset(transit[0])


def test_serpapi_hotels_includes_required_dates(monkeypatch):
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"properties": [{"name": "Tokyo Stay", "rate_per_night": {"lowest": "$180"}}]}

    def fake_get(url, *, params, timeout):
        calls.append({"url": url, "params": params, "timeout": timeout})
        return Response()

    monkeypatch.setattr("src.tools.serpapi_tools.requests.get", fake_get)

    state = TravelState()
    result = search_hotels(
        state,
        Settings(None, "serp-key", None, None, allow_demo_fallbacks=False),
        {"destination": "Japan", "start_date": "2026-10-10", "days": 5},
    )

    assert calls[0]["params"]["engine"] == "google_hotels"
    assert calls[0]["params"]["q"] == "hotels in Japan"
    assert calls[0]["params"]["check_in_date"] == "2026-10-10"
    assert calls[0]["params"]["check_out_date"] == "2026-10-15"
    assert calls[0]["params"]["api_key"] == "serp-key"
    assert result == [{"name": "Tokyo Stay", "rate_per_night": {"lowest": "$180"}}]


def test_serpapi_errors_do_not_expose_api_key(monkeypatch):
    class Response:
        status_code = 400
        url = "https://serpapi.com/search.json?engine=google_flights&api_key=secret-key"
        text = "arrival_id is invalid"

        def raise_for_status(self):
            raise requests.HTTPError("400 Client Error: Bad Request for url: " + self.url)

        def json(self):
            return {"error": "arrival_id is invalid"}

    monkeypatch.setattr("src.tools.serpapi_tools.requests.get", lambda *args, **kwargs: Response())

    state = TravelState()
    settings = Settings(None, "secret-key", None, None, allow_demo_fallbacks=False)

    with pytest.raises(ToolExecutionError) as exc:
        search_flights(
            state,
            settings,
            {"origin": "SFO", "destination": "And I Want To", "start_date": "2026-09-01"},
        )

    message = str(exc.value)
    assert "secret-key" not in message
    assert "api_key" not in message
    assert "arrival_id is invalid" in message


def test_google_maps_parser_raises_clear_error_for_malformed_payload():
    with pytest.raises(RuntimeError, match="missing route duration"):
        _extract_distance_matrix_result({"rows": [{"elements": [{"status": "OK"}]}]}, {"origin": "A", "destination": "B"})


def test_google_maps_uses_routes_api_v2(monkeypatch):
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return [{"condition": "ROUTE_EXISTS", "duration": "900s", "distanceMeters": 1200}]

    def fake_post(url, *, headers, json, timeout):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return Response()

    monkeypatch.setattr("src.tools.google_maps_tools.requests.post", fake_post)

    result = _estimate_google_transit(
        Settings(None, None, None, "maps-key"),
        {"origin": "Shinjuku", "destination": "Asakusa", "mode": "transit"},
    )

    assert calls[0]["url"] == "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
    assert calls[0]["headers"]["X-Goog-Api-Key"] == "maps-key"
    assert "duration" in calls[0]["headers"]["X-Goog-FieldMask"]
    assert calls[0]["json"]["origins"][0]["waypoint"]["address"] == "Shinjuku"
    assert calls[0]["json"]["travelMode"] == "TRANSIT"
    assert result[0]["duration_minutes"] == 15
    assert result[0]["source"] == "google_routes"


def test_google_maps_raises_actionable_routes_permission_error(monkeypatch):
    class Response:
        status_code = 403
        text = "Routes API has not been used in project before or it is disabled."

        def raise_for_status(self):
            raise requests.HTTPError("403 Client Error: Forbidden")

        def json(self):
            return {
                "error": {
                    "code": 403,
                    "message": "Routes API has not been used in project before or it is disabled.",
                    "status": "PERMISSION_DENIED",
                }
            }

    def fake_post(*args, **kwargs):
        return Response()

    monkeypatch.setattr("src.tools.google_maps_tools.requests.post", fake_post)

    with pytest.raises(RuntimeError) as exc:
        _estimate_google_transit(
            Settings(None, None, None, "maps-key"),
            {"origin": "Shinjuku", "destination": "Asakusa", "mode": "transit"},
        )

    error = str(exc.value)
    assert "Google Routes API permission denied" in error
    assert "enable the Routes API" in error
    assert "PERMISSION_DENIED" in error


def test_google_places_uses_places_api_new_text_search(monkeypatch):
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "places": [
                    {
                        "id": "abc",
                        "displayName": {"text": "Vegan Ramen"},
                        "formattedAddress": "Tokyo",
                        "rating": 4.7,
                    }
                ]
            }

    def fake_post(url, *, headers, json, timeout):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return Response()

    monkeypatch.setattr("src.tools.google_places_tools.requests.post", fake_post)

    result = _search_places(Settings(None, None, None, "maps-key"), {"city": "Tokyo", "dietary": "vegetarian"})

    assert calls[0]["url"] == "https://places.googleapis.com/v1/places:searchText"
    assert calls[0]["headers"]["X-Goog-Api-Key"] == "maps-key"
    assert "places.displayName" in calls[0]["headers"]["X-Goog-FieldMask"]
    assert calls[0]["json"]["textQuery"] == "vegetarian restaurants in Tokyo"
    assert result == [
        {
            "name": "Vegan Ramen",
            "city": "Tokyo",
            "rating": 4.7,
            "address": "Tokyo",
            "place_id": "abc",
            "source": "google_places_new",
        }
    ]
