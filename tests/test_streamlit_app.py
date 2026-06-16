from streamlit.testing.v1 import AppTest

from src.state.travel_state import WorkflowState


REQUIRED_ENV_KEYS = (
    "OPENAI_API_KEY",
    "SERPAPI_API_KEY",
    "TAVILY_API_KEY",
    "GOOGLE_MAPS_API_KEY",
    "ALLOW_DEMO_FALLBACKS",
)


def test_streamlit_app_runs_without_local_secrets(monkeypatch):
    for key in REQUIRED_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=10)

    assert not app.exception


def test_streamlit_app_strict_mode_stops_when_keys_are_missing(monkeypatch):
    for key in REQUIRED_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=10)
    app.button[0].click().run(timeout=10)

    state = app.session_state["travel_state"]
    assert not app.exception
    assert state.current_state == WorkflowState.FAILED
    assert not state.itinerary


def test_streamlit_app_fallback_mode_builds_draft_itinerary(monkeypatch):
    for key in REQUIRED_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("ALLOW_DEMO_FALLBACKS", "true")

    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=10)
    app.button[0].click().run(timeout=10)

    state = app.session_state["travel_state"]
    assert not app.exception
    assert state.current_state == WorkflowState.AWAITING_CALENDAR_APPROVAL
    assert len(state.itinerary) == 10
