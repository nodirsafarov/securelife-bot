"""Centralized configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


# Load .env from project root if present.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _required(key: str) -> str:
    """Read a required env var or fail fast with a clear error."""
    value = os.getenv(key, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {key}. "
            f"Copy .env.example to .env and fill it in."
        )
    return value


def _int(key: str, default: int) -> int:
    raw = os.getenv(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _id_list(key: str) -> list[int]:
    raw = os.getenv(key, "").strip()
    if not raw:
        return []
    out: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(part))
        except ValueError:
            continue
    return out


@dataclass(frozen=True)
class Config:
    telegram_token: str
    gemini_api_key: str
    gemini_model: str
    bot_name: str
    bot_username: str
    rate_limit_per_hour: int
    db_path: Path
    log_level: str
    default_language: str
    admin_user_ids: list[int]
    max_input_length: int
    telegram_proxy: str | None

    @classmethod
    def from_env(cls) -> "Config":
        db_raw = os.getenv("DB_PATH", "securelife.db").strip()
        db_path = Path(db_raw)
        if not db_path.is_absolute():
            db_path = PROJECT_ROOT / db_path

        default_lang = os.getenv("DEFAULT_LANGUAGE", "uz").strip().lower()
        if default_lang not in ("uz", "en"):
            default_lang = "uz"

        return cls(
            telegram_token=_required("TELEGRAM_BOT_TOKEN"),
            gemini_api_key=_required("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp").strip(),
            bot_name=os.getenv("BOT_NAME", "SecureLife").strip(),
            bot_username=os.getenv("BOT_USERNAME", "securelife_bot").strip(),
            rate_limit_per_hour=_int("RATE_LIMIT_PER_HOUR", 30),
            db_path=db_path,
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
            default_language=default_lang,
            admin_user_ids=_id_list("ADMIN_USER_IDS"),
            max_input_length=_int("MAX_INPUT_LENGTH", 4000),
            telegram_proxy=(os.getenv("TELEGRAM_PROXY", "").strip() or None),
        )
