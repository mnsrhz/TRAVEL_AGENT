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
    app.button(key="start_planning").click().run(timeout=10)

    state = app.session_state["travel_state"]
    assert not app.exception
    assert state.current_state == WorkflowState.AWAITING_PREFERENCE_APPROVAL

    app.button(key="approve_preference_confirmation").click().run(timeout=10)

    state = app.session_state["travel_state"]
    assert state.current_state == WorkflowState.FAILED
    assert not state.itinerary


def test_streamlit_app_fallback_mode_requires_each_approval_gate(monkeypatch):
    for key in REQUIRED_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("ALLOW_DEMO_FALLBACKS", "true")

    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=10)
    app.button(key="start_planning").click().run(timeout=10)

    state = app.session_state["travel_state"]
    assert not app.exception
    assert state.current_state == WorkflowState.AWAITING_PREFERENCE_APPROVAL

    app.button(key="approve_preference_confirmation").click().run(timeout=10)
    state = app.session_state["travel_state"]
    assert state.current_state == WorkflowState.AWAITING_DESTINATION_APPROVAL

    app.button(key="approve_destination_city_split").click().run(timeout=10)
    state = app.session_state["travel_state"]
    assert state.current_state == WorkflowState.AWAITING_HIGH_RISK_DAY_APPROVAL
    assert len(state.itinerary) == 10

    app.button(key="approve_high_risk_day").click().run(timeout=10)
    state = app.session_state["travel_state"]
    assert state.current_state == WorkflowState.AWAITING_ITINERARY_APPROVAL

    app.button(key="approve_final_itinerary").click().run(timeout=10)
    state = app.session_state["travel_state"]
    assert state.current_state == WorkflowState.AWAITING_CALENDAR_APPROVAL
    assert len(state.itinerary) == 10
    assert state.approvals == {
        "preference_confirmation": True,
        "destination_city_split": True,
        "high_risk_day": True,
        "final_itinerary": True,
    }


def test_streamlit_app_exports_markdown_and_trace_before_calendar_ics(monkeypatch):
    for key in REQUIRED_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("ALLOW_DEMO_FALLBACKS", "true")

    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=10)
    app.button(key="start_planning").click().run(timeout=10)
    for key in (
        "approve_preference_confirmation",
        "approve_destination_city_split",
        "approve_high_risk_day",
        "approve_final_itinerary",
    ):
        app.button(key=key).click().run(timeout=10)

    state = app.session_state["travel_state"]
    assert state.current_state == WorkflowState.AWAITING_CALENDAR_APPROVAL
    download_buttons = app.get("download_button")
    assert len(download_buttons) == 2
    assert [button.label for button in download_buttons] == [
        "Download itinerary markdown",
        "Download trace JSON",
    ]

    app.button(key="approve_calendar_creation").click().run(timeout=10)

    state = app.session_state["travel_state"]
    assert state.current_state == WorkflowState.COMPLETE
    assert state.generated_ics
    assert [button.label for button in app.get("download_button")] == [
        "Download itinerary markdown",
        "Download calendar ICS",
        "Download trace JSON",
    ]


def test_streamlit_app_new_submission_resets_previous_trip_state(monkeypatch):
    for key in REQUIRED_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("ALLOW_DEMO_FALLBACKS", "true")

    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=10)
    app.button(key="start_planning").click().run(timeout=10)
    for key in (
        "approve_preference_confirmation",
        "approve_destination_city_split",
        "approve_high_risk_day",
        "approve_final_itinerary",
        "approve_calendar_creation",
    ):
        app.button(key=key).click().run(timeout=10)

    completed_state = app.session_state["travel_state"]
    assert completed_state.current_state == WorkflowState.COMPLETE
    assert completed_state.generated_ics

    app.number_input[0].set_value(3).run(timeout=10)
    app.button(key="start_planning").click().run(timeout=10)

    new_state = app.session_state["travel_state"]
    assert new_state.current_state == WorkflowState.AWAITING_PREFERENCE_APPROVAL
    assert new_state.user_input["days"] == 3
    assert new_state.approvals == {}
    assert new_state.generated_ics is None
    assert new_state.itinerary == []


def test_streamlit_app_calendar_export_error_is_shown_without_crashing(monkeypatch):
    for key in REQUIRED_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("ALLOW_DEMO_FALLBACKS", "true")

    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=10)
    app.button(key="start_planning").click().run(timeout=10)
    for key in (
        "approve_preference_confirmation",
        "approve_destination_city_split",
        "approve_high_risk_day",
        "approve_final_itinerary",
    ):
        app.button(key=key).click().run(timeout=10)

    state = app.session_state["travel_state"]
    state.itinerary[0]["events"][0].pop("start")
    app.session_state["travel_state"] = state
    app.button(key="approve_calendar_creation").click().run(timeout=10)

    state = app.session_state["travel_state"]
    assert not app.exception
    assert state.current_state == WorkflowState.FAILED
    assert state.generated_ics is None
    assert state.errors
