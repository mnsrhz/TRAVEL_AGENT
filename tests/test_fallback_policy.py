import pytest

from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools.google_maps_tools import estimate_transit
from src.tools.google_places_tools import search_restaurants
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
    assert search_flights(state, settings, {"origin": "SFO", "destination": "Tokyo"})
    assert search_hotels(state, settings, {"destination": "Tokyo"})
    assert search_attractions(state, settings, {"destination": "Japan"})
    assert search_restaurants(state, settings, {"city": "Tokyo", "dietary": "vegetarian"})
    assert estimate_transit(state, settings, {"origin": "Shinjuku", "destination": "Asakusa"})
