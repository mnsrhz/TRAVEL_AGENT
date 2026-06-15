import re


REQUIRED_FIELDS = ("destination", "days", "origin", "start_date", "budget", "pace", "dietary")


def missing_required_fields(user_input: dict) -> list[str]:
    return [field for field in REQUIRED_FIELDS if not user_input.get(field)]


def normalize_preferences(user_input: dict) -> dict:
    preferences = dict(user_input)
    preferences["days"] = _coerce_int(preferences.get("days"), default=10, minimum=1)
    preferences["budget"] = _coerce_int(preferences.get("budget"), default=3500, minimum=0)
    preferences["pace"] = _coerce_text(preferences.get("pace"), default="moderate").lower()
    preferences["dietary"] = _coerce_text(preferences.get("dietary"), default="none").lower()
    return preferences


def _coerce_int(value: object, *, default: int, minimum: int) -> int:
    if value is None:
        return default
    match = re.search(r"\d+(?:\.\d+)?", str(value).replace(",", ""))
    if not match:
        return default
    return max(minimum, int(float(match.group(0))))


def _coerce_text(value: object, *, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default
