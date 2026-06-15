REQUIRED_FIELDS = ("destination", "days", "origin", "start_date", "budget", "pace", "dietary")


def missing_required_fields(user_input: dict) -> list[str]:
    return [field for field in REQUIRED_FIELDS if not user_input.get(field)]


def normalize_preferences(user_input: dict) -> dict:
    preferences = dict(user_input)
    preferences["days"] = int(preferences.get("days", 10))
    preferences["budget"] = int(str(preferences.get("budget", "3500")).replace("$", "").replace(",", ""))
    preferences["pace"] = preferences.get("pace", "moderate").lower()
    preferences["dietary"] = preferences.get("dietary", "none").lower()
    return preferences
