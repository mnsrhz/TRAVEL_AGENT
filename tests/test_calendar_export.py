import pytest

from src.exports.itinerary_export import itinerary_to_markdown
from src.tools.calendar_tools import CalendarExportError, generate_ics


def sample_itinerary():
    return [
        {
            "day": 1,
            "date": "2026-10-10",
            "events": [
                {
                    "type": "attraction",
                    "title": "Visit Senso-ji Temple",
                    "start": "2026-10-10T09:00:00",
                    "end": "2026-10-10T10:30:00",
                    "location": "Asakusa, Tokyo",
                    "description": "Free entry. Backup: Nakamise shopping street.",
                    "cost": "$0",
                    "source": "demo",
                }
            ],
        }
    ]


def test_generate_ics_contains_event_fields():
    ics_bytes = generate_ics(sample_itinerary())
    content = ics_bytes.decode("utf-8")
    assert "BEGIN:VCALENDAR" in content
    assert "SUMMARY:Visit Senso-ji Temple" in content
    assert "LOCATION:Asakusa\\, Tokyo" in content
    assert "END:VCALENDAR" in content


def test_itinerary_markdown_contains_day_and_event():
    markdown = itinerary_to_markdown(sample_itinerary())
    assert "## Day 1 - 2026-10-10" in markdown
    assert "Visit Senso-ji Temple" in markdown
    assert "Asakusa, Tokyo" in markdown


def test_generate_ics_accepts_z_suffix_and_emits_utc():
    itinerary = sample_itinerary()
    itinerary[0]["events"][0]["start"] = "2026-10-10T09:00:00Z"
    itinerary[0]["events"][0]["end"] = "2026-10-10T10:30:00Z"
    content = generate_ics(itinerary).decode("utf-8")
    assert "DTSTART:20261010T090000Z" in content
    assert "DTEND:20261010T103000Z" in content


def test_generate_ics_treats_naive_times_as_utc():
    content = generate_ics(sample_itinerary()).decode("utf-8")
    assert "DTSTART:20261010T090000Z" in content
    assert "DTEND:20261010T103000Z" in content


def test_generate_ics_raises_clear_error_for_missing_event_field():
    itinerary = sample_itinerary()
    del itinerary[0]["events"][0]["start"]

    with pytest.raises(CalendarExportError, match="Missing required event field: start"):
        generate_ics(itinerary)


def test_itinerary_markdown_escapes_special_characters_and_newlines():
    itinerary = sample_itinerary()
    itinerary[0]["events"][0]["title"] = "Lunch *special* [vegan]"
    itinerary[0]["events"][0]["description"] = "Line one\nLine two"

    markdown = itinerary_to_markdown(itinerary)

    assert "Lunch \\*special\\* \\[vegan\\]" in markdown
    assert "Line one Line two" in markdown
