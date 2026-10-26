"""Validated project settings loaded from the repository .env file."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIMO_PRO_MODEL = "mimo-v2.6-pro"
DEFAULT_OLLAMA_MODEL = "k2"
DEFAULT_OLLAMA_URL = "http://localhost:11434/v1/"
DEFAULT_MIMO_URL = "https://api.xiaomimimo.com/v1"


@dataclass(frozen=True)
class Settings:
    ollama_model: str
    ollama_base_url: str
    mimo_api_key: str = field(repr=False)
    mimo_base_url: str | None = None
    mimo_model: str = MIMO_PRO_MODEL
    anthropic_api_key: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        if not self.ollama_model.strip():
            raise ValueError("OLLAMA_MODEL must not be empty.")
        _validate_url("OLLAMA_BASE_URL", self.ollama_base_url)
        if self.mimo_base_url:
            _validate_url("MIMO_BASE_URL", self.mimo_base_url)
        if self.mimo_model != MIMO_PRO_MODEL:
            raise ValueError(f"Heavy tasks must use {MIMO_PRO_MODEL!r}.")

    def get_mimo_base_url(self) -> str:
        if self.mimo_base_url:
            return self.mimo_base_url
        if self.mimo_api_key.startswith(("tp-", "ttp-")):
            raise RuntimeError(
                "Set MIMO_BASE_URL from your Token Plan page; its region varies."
            )
        return DEFAULT_MIMO_URL


def _validate_url(name: str, value: str) -> None:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{name} must be a full http:// or https:// URL.")


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    return Settings(
        ollama_model=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip(),
        ollama_base_url=os.getenv(
            "OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL).strip(),
        mimo_api_key=os.getenv("MIMO_API_KEY", "").strip(),
        mimo_base_url=os.getenv("MIMO_BASE_URL", "").strip() or None,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "").strip(),
    )


settings = load_settings()
