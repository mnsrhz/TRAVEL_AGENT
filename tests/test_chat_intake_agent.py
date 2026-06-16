from datetime import date

from src.agents.chat_intake_agent import extract_preferences, ingest_user_message, missing_required_fields
from src.config.settings import Settings


def test_chat_intake_extracts_trip_details_from_plain_english():
    preferences, reply, ready = ingest_user_message(
        {},
        "Plan a 10 day Japan trip from SFO starting 2026-10-10, vegetarian, moderate pace, budget $3500.",
    )

    assert ready is True
    assert reply.startswith("I have the essentials")
    assert preferences == {
        "destination": "Japan",
        "days": 10,
        "origin": "SFO",
        "start_date": "2026-10-10",
        "budget": 3500,
        "pace": "moderate",
        "dietary": "vegetarian",
    }


def test_chat_intake_asks_one_follow_up_for_missing_detail():
    preferences, reply, ready = ingest_user_message({}, "I want a relaxed 7 day trip to Italy from NYC.")

    assert ready is False
    assert preferences["destination"] == "Italy"
    assert preferences["days"] == 7
    assert preferences["origin"] == "NYC"
    assert missing_required_fields(preferences) == ["start_date", "budget", "dietary"]
    assert reply == "When would you like to start the trip?"


def test_chat_intake_merges_follow_up_answers():
    preferences, _, ready = ingest_user_message({}, "I want a relaxed 7 day trip to Italy from NYC.")
    assert ready is False

    preferences, reply, ready = ingest_user_message(preferences, "Start on 2026-09-05 with a $4200 budget and no dietary restrictions.")

    assert ready is True
    assert preferences["start_date"] == "2026-09-05"
    assert preferences["budget"] == 4200
    assert preferences["dietary"] == "none"
    assert reply.startswith("I have the essentials")


def test_chat_intake_uses_missing_field_context_for_short_origin_answer():
    existing = {
        "destination": "Japan",
        "days": 10,
        "start_date": "2026-10-10",
        "budget": 3500,
        "pace": "moderate",
        "dietary": "vegetarian",
    }

    preferences, reply, ready = ingest_user_message(existing, "SFO")

    assert ready is True
    assert preferences["origin"] == "SFO"
    assert reply.startswith("I have the essentials")


def test_chat_intake_handles_contextual_follow_up_without_live_llm(monkeypatch):
    def fail_live_call(settings, existing, message):
        raise AssertionError("Live extraction should not be called for a contextual short answer")

    monkeypatch.setattr("src.agents.chat_intake_agent._extract_preferences_with_openai", fail_live_call)
    existing = {
        "destination": "Japan",
        "days": 10,
        "start_date": "2026-10-10",
        "budget": 3500,
        "pace": "moderate",
        "dietary": "vegetarian",
    }

    preferences, reply, ready = ingest_user_message(
        existing,
        "SFO",
        Settings("openai-key", None, None, None),
    )

    assert ready is True
    assert preferences["origin"] == "SFO"
    assert reply.startswith("I have the essentials")


def test_chat_intake_resolves_yearless_start_date_from_current_date(monkeypatch):
    monkeypatch.setattr("src.agents.chat_intake_agent._today", lambda: date(2026, 6, 16))
    existing = {
        "destination": "Japan",
        "days": 10,
        "origin": "SFO",
        "budget": 3500,
        "pace": "moderate",
        "dietary": "vegetarian",
    }

    preferences, reply, ready = ingest_user_message(existing, "Sep 1st")

    assert ready is True
    assert preferences["start_date"] == "2026-09-01"
    assert reply.startswith("I have the essentials")


def test_chat_intake_rolls_past_yearless_dates_to_next_year(monkeypatch):
    monkeypatch.setattr("src.agents.chat_intake_agent._today", lambda: date(2026, 9, 2))

    preferences, _, ready = ingest_user_message(
        {
            "destination": "Japan",
            "days": 10,
            "origin": "SFO",
            "budget": 3500,
            "pace": "moderate",
            "dietary": "vegetarian",
        },
        "Sep 1st",
    )

    assert ready is True
    assert preferences["start_date"] == "2027-09-01"


def test_chat_intake_prefers_current_date_local_parse_over_live_invented_year(monkeypatch):
    monkeypatch.setattr("src.agents.chat_intake_agent._today", lambda: date(2026, 6, 16))
    monkeypatch.setattr(
        "src.agents.chat_intake_agent._extract_preferences_with_openai",
        lambda settings, existing, message: {"start_date": "2023-09-01"},
    )

    preferences = extract_preferences(
        "Sep 1st",
        settings=Settings("openai-key", None, None, None),
        existing_preferences={},
    )

    assert preferences["start_date"] == "2026-09-01"
