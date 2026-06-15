from __future__ import annotations

import os
from dataclasses import dataclass


REQUIRED_API_KEYS = (
    "OPENAI_API_KEY",
    "SERPAPI_API_KEY",
    "TAVILY_API_KEY",
    "GOOGLE_MAPS_API_KEY",
)


def _parse_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    serpapi_api_key: str | None
    tavily_api_key: str | None
    google_maps_api_key: str | None
    allow_demo_fallbacks: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            serpapi_api_key=os.getenv("SERPAPI_API_KEY") or None,
            tavily_api_key=os.getenv("TAVILY_API_KEY") or None,
            google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY") or None,
            allow_demo_fallbacks=_parse_bool(os.getenv("ALLOW_DEMO_FALLBACKS")),
        )

    @property
    def mode_label(self) -> str:
        return "Live + fallback" if self.allow_demo_fallbacks else "Strict live"

    @property
    def key_map(self) -> dict[str, str | None]:
        return {
            "OPENAI_API_KEY": self.openai_api_key,
            "SERPAPI_API_KEY": self.serpapi_api_key,
            "TAVILY_API_KEY": self.tavily_api_key,
            "GOOGLE_MAPS_API_KEY": self.google_maps_api_key,
        }

    @property
    def missing_keys(self) -> list[str]:
        return [key for key, value in self.key_map.items() if not value]

    def has_key(self, key: str) -> bool:
        return bool(self.key_map.get(key))
