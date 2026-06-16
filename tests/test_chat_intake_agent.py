from src.agents.chat_intake_agent import ingest_user_message, missing_required_fields


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
