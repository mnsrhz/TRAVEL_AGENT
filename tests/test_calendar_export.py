from src.exports.itinerary_export import itinerary_to_markdown
from src.tools.calendar_tools import generate_ics


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
