from src.config.settings import Settings


def test_settings_defaults_to_strict_mode_when_flag_missing(monkeypatch):
    monkeypatch.delenv("ALLOW_DEMO_FALLBACKS", raising=False)
    settings = Settings.from_env()
    assert settings.allow_demo_fallbacks is False
    assert settings.mode_label == "Strict live"


def test_settings_parses_fallback_flag(monkeypatch):
    monkeypatch.setenv("ALLOW_DEMO_FALLBACKS", "true")
    settings = Settings.from_env()
    assert settings.allow_demo_fallbacks is True
    assert settings.mode_label == "Live + fallback"


def test_settings_reports_missing_keys(monkeypatch):
    for key in ("OPENAI_API_KEY", "SERPAPI_API_KEY", "TAVILY_API_KEY", "GOOGLE_MAPS_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    settings = Settings.from_env()
    assert settings.missing_keys == [
        "OPENAI_API_KEY",
        "SERPAPI_API_KEY",
        "TAVILY_API_KEY",
        "GOOGLE_MAPS_API_KEY",
    ]
    assert settings.has_key("OPENAI_API_KEY") is False
