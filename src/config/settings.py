from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


REQUIRED_API_KEYS = (
    "OPENAI_API_KEY",
    "SERPAPI_API_KEY",
    "TAVILY_API_KEY",
    "GOOGLE_MAPS_API_KEY",
)


ENV_FIELD_MAP = {
    "OPENAI_API_KEY": "openai_api_key",
    "SERPAPI_API_KEY": "serpapi_api_key",
    "TAVILY_API_KEY": "tavily_api_key",
    "GOOGLE_MAPS_API_KEY": "google_maps_api_key",
}

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def _parse_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _clean_env(value: str | None) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _lookup_setting(env: Mapping[str, str], secrets: Mapping[str, object] | None, key: str) -> str | None:
    env_value = _clean_env(env.get(key))
    if env_value:
        return env_value
    if secrets is None:
        return None
    return _clean_env(str(secrets.get(key, "")))


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    serpapi_api_key: str | None
    tavily_api_key: str | None
    google_maps_api_key: str | None
    openai_model: str = DEFAULT_OPENAI_MODEL
    allow_demo_fallbacks: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        return cls.from_sources(os.environ, None)

    @classmethod
    def from_sources(cls, env: Mapping[str, str], secrets: Mapping[str, object] | None = None) -> "Settings":
        return cls(
            openai_api_key=_lookup_setting(env, secrets, "OPENAI_API_KEY"),
            serpapi_api_key=_lookup_setting(env, secrets, "SERPAPI_API_KEY"),
            tavily_api_key=_lookup_setting(env, secrets, "TAVILY_API_KEY"),
            google_maps_api_key=_lookup_setting(env, secrets, "GOOGLE_MAPS_API_KEY"),
            openai_model=_lookup_setting(env, secrets, "OPENAI_MODEL") or DEFAULT_OPENAI_MODEL,
            allow_demo_fallbacks=_parse_bool(_lookup_setting(env, secrets, "ALLOW_DEMO_FALLBACKS")),
        )

    @property
    def mode_label(self) -> str:
        return "Live + fallback" if self.allow_demo_fallbacks else "Strict live"

    @property
    def key_map(self) -> dict[str, str | None]:
        return {key: getattr(self, ENV_FIELD_MAP[key]) for key in REQUIRED_API_KEYS}

    @property
    def missing_keys(self) -> list[str]:
        return [key for key, value in self.key_map.items() if not value]

    def has_key(self, key: str) -> bool:
        return bool(self.key_map.get(key))
