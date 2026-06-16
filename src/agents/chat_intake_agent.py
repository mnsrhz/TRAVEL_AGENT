from __future__ import annotations

import calendar
import json
import re
from datetime import date, datetime
from typing import Any

from src.agents.preference_agent import REQUIRED_FIELDS, missing_required_fields
from src.config.settings import Settings


FOLLOW_UP_QUESTIONS = {
    "destination": "Where would you like to go?",
    "days": "How many days should the trip be?",
    "origin": "Where will you be traveling from?",
    "start_date": "When would you like to start the trip?",
    "budget": "What budget should I plan around?",
    "pace": "What pace would you prefer: relaxed, moderate, or packed?",
    "dietary": "Any dietary preferences or restrictions?",
}


def ingest_user_message(
    existing_preferences: dict[str, Any],
    message: str,
    settings: Settings | None = None,
) -> tuple[dict[str, Any], str, bool]:
    preferences = dict(existing_preferences)
    preferences.update(extract_preferences_locally(message))
    preferences.update(_extract_contextual_follow_up(existing_preferences, preferences, message))
    if missing_required_fields(preferences) and settings and settings.openai_api_key:
        preferences.update(extract_preferences(message, settings=settings, existing_preferences=existing_preferences))
        preferences.update(_extract_contextual_follow_up(existing_preferences, preferences, message))
    missing = missing_required_fields(preferences)
    if missing:
        return preferences, FOLLOW_UP_QUESTIONS[missing[0]], False
    return preferences, "I have the essentials. Please review the trip preferences below.", True


def extract_preferences(
    message: str,
    *,
    settings: Settings | None = None,
    existing_preferences: dict[str, Any] | None = None,
) -> dict[str, Any]:
    local_preferences = extract_preferences_locally(message)
    if settings and settings.openai_api_key:
        live_preferences = _extract_preferences_with_openai(settings, existing_preferences or {}, message)
        if live_preferences:
            return {**live_preferences, **local_preferences}
    return local_preferences


def extract_preferences_locally(message: str) -> dict[str, Any]:
    text = " ".join(message.strip().split())
    extracted: dict[str, Any] = {}
    if not text:
        return extracted

    destination = _extract_destination(text)
    if destination:
        extracted["destination"] = destination

    days = _extract_days(text)
    if days:
        extracted["days"] = days

    origin = _extract_origin(text)
    if origin:
        extracted["origin"] = origin

    start_date = _extract_start_date(text)
    if start_date:
        extracted["start_date"] = start_date

    budget = _extract_budget(text)
    if budget is not None:
        extracted["budget"] = budget

    pace = _extract_pace(text)
    if pace:
        extracted["pace"] = pace

    dietary = _extract_dietary(text)
    if dietary:
        extracted["dietary"] = dietary

    return extracted


def _extract_preferences_with_openai(settings: Settings, existing_preferences: dict[str, Any], message: str) -> dict[str, Any]:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract travel planning preferences from the user's message. "
                        "Return only JSON with any of these keys when present: "
                        f"{', '.join(REQUIRED_FIELDS)}. Use ISO YYYY-MM-DD for start_date, "
                        f"today is {_today().isoformat()}, and dates without a year must use the next upcoming occurrence. "
                        "integer values for days and budget, and lowercase strings for pace and dietary. "
                        "Do not invent missing values."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({"existing_preferences": existing_preferences, "latest_message": message}),
                },
            ],
        )
        payload = response.choices[0].message.content or "{}"
        parsed = json.loads(payload)
    except Exception:
        return {}
    return _clean_live_preferences(parsed)


def _extract_contextual_follow_up(
    existing_preferences: dict[str, Any],
    merged_preferences: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    missing_before = missing_required_fields(existing_preferences)
    if not missing_before:
        return {}
    current_field = missing_before[0]
    if merged_preferences.get(current_field):
        return {}
    value = _coerce_follow_up_value(current_field, message)
    return {current_field: value} if value not in {None, ""} else {}


def _coerce_follow_up_value(field: str, message: str) -> Any:
    text = message.strip()
    if not text:
        return None
    if field == "origin":
        origin = _clean_place(text)
        return origin.upper() if len(origin) == 3 else origin
    if field == "destination":
        return _clean_place(text)
    if field == "days":
        return _extract_days(text)
    if field == "start_date":
        return _extract_start_date(text)
    if field == "budget":
        return _extract_budget(text)
    if field == "pace":
        return _extract_pace(text)
    if field == "dietary":
        return _extract_dietary(text) or _clean_place(text).lower()
    return None


def _clean_live_preferences(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for field in REQUIRED_FIELDS:
        value = payload.get(field)
        if value in {None, ""}:
            continue
        if field in {"days", "budget"}:
            try:
                cleaned[field] = max(0 if field == "budget" else 1, int(float(str(value).replace(",", ""))))
            except ValueError:
                continue
        elif field == "start_date":
            date_value = _format_date(str(value), "%Y-%m-%d")
            if date_value:
                cleaned[field] = date_value
        elif field in {"pace", "dietary"}:
            cleaned[field] = str(value).strip().lower()
        else:
            cleaned[field] = str(value).strip()
    return cleaned


def _extract_destination(text: str) -> str | None:
    patterns = [
        r"\b\d{1,2}\s*(?:day|days|night|nights)\s+([A-Za-z][A-Za-z\s]+?)\s+(?:trip|travel|vacation|holiday)\b",
        r"(?:trip|travel|vacation|holiday)\s+(?:to|in)\s+([A-Za-z][A-Za-z\s]+?)(?=\s+(?:from|starting|start|on|with|around|under|for|budget)|[,\.]|$)",
        r"(?:to|visit|visiting)\s+([A-Za-z][A-Za-z\s]+?)(?=\s+(?:from|starting|start|on|with|around|under|for|budget)|[,\.]|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            destination = _clean_place(match.group(1))
            if destination and destination.lower() not in {"trip", "travel", "vacation"}:
                return destination
    return None


def _extract_days(text: str) -> int | None:
    match = re.search(r"\b(\d{1,2})\s*(?:day|days|night|nights)\b", text, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _extract_origin(text: str) -> str | None:
    match = re.search(
        r"(?:from|departing from|leaving from)\s+([A-Za-z]{3}|[A-Za-z][A-Za-z\s]+?)(?=\s+(?:to|starting|start|on|with|around|under|for|budget)|[,\.]|$)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    origin = _clean_place(match.group(1))
    return origin.upper() if len(origin) == 3 else origin


def _extract_start_date(text: str) -> str | None:
    iso = re.search(r"\b(20\d{2}-\d{1,2}-\d{1,2})\b", text)
    if iso:
        return _format_date(iso.group(1), "%Y-%m-%d")

    month_names = "|".join(calendar.month_name[1:] + calendar.month_abbr[1:])
    explicit_year = re.search(
        rf"\b(?:start(?:ing)?|on)?\s*({month_names})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,)?\s+(20\d{{2}})\b",
        text,
        flags=re.IGNORECASE,
    )
    if explicit_year:
        return _format_date(
            f"{explicit_year.group(1)} {explicit_year.group(2)} {explicit_year.group(3)}",
            "%B %d %Y",
        ) or _format_date(f"{explicit_year.group(1)} {explicit_year.group(2)} {explicit_year.group(3)}", "%b %d %Y")

    yearless = re.search(
        rf"\b(?:start(?:ing)?|on)?\s*({month_names})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b",
        text,
        flags=re.IGNORECASE,
    )
    if not yearless:
        return None
    return _resolve_yearless_month_day(yearless.group(1), yearless.group(2))


def _extract_budget(text: str) -> int | None:
    match = re.search(r"(?:\$|budget\s*(?:of|around|is)?\s*\$?)(\d[\d,]*)", text, flags=re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    match = re.search(r"\b(\d[\d,]*)\s*(?:usd|dollars|budget)\b", text, flags=re.IGNORECASE)
    return int(match.group(1).replace(",", "")) if match else None


def _extract_pace(text: str) -> str | None:
    match = re.search(r"\b(relaxed|moderate|packed)\b", text, flags=re.IGNORECASE)
    return match.group(1).lower() if match else None


def _extract_dietary(text: str) -> str | None:
    if re.search(r"\b(no dietary|no restrictions|none)\b", text, flags=re.IGNORECASE):
        return "none"
    match = re.search(r"\b(vegetarian|vegan|halal|kosher|gluten[-\s]?free|pescatarian)\b", text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower().replace(" ", "-")


def _clean_place(value: str) -> str:
    value = re.sub(
        r"^\s*(?:and\s+)?(?:i\s+)?(?:want|would\s+like|need|plan|hope)\s+to\s+(?:go\s+to|travel\s+to|visit|see)?\s*",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"^\s*(?:go|travel)\s+to\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(trip|travel|vacation|holiday)\b", "", value, flags=re.IGNORECASE)
    return " ".join(value.strip(" ,.-").split()).title()


def _format_date(value: str, date_format: str) -> str | None:
    try:
        return datetime.strptime(value, date_format).date().isoformat()
    except ValueError:
        return None


def _resolve_yearless_month_day(month: str, day: str) -> str | None:
    parsed = _parse_month_day(month, day, _today().year)
    if not parsed:
        return None
    if parsed < _today():
        parsed = _parse_month_day(month, day, _today().year + 1)
    return parsed.isoformat() if parsed else None


def _parse_month_day(month: str, day: str, year: int) -> date | None:
    for date_format in ("%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(f"{month} {day} {year}", date_format).date()
        except ValueError:
            continue
    return None


def _today() -> date:
    return date.today()
