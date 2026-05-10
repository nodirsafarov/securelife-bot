"""SQLite-backed persistence for user language and rate limiting.

Privacy notes:
- We store a per-user language preference (en/uz) keyed by Telegram
  user_id. We do NOT store message content.
- Rate-limit table stores only timestamps of events, no content.
- All operations run in a worker thread via asyncio.to_thread so the
  asyncio event loop is never blocked by sqlite3.
"""
from __future__ import annotations

import asyncio
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id   INTEGER PRIMARY KEY,
    language  TEXT    NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS rate_events (
    user_id   INTEGER NOT NULL,
    ts        INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rate_user_ts ON rate_events(user_id, ts);

CREATE TABLE IF NOT EXISTS analyses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    ts          INTEGER NOT NULL,
    verdict     TEXT    NOT NULL,
    risk_score  INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_analyses_user_ts ON analyses(user_id, ts);
"""


class Database:
    """Async-friendly SQLite wrapper with a single shared connection."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()
        # `check_same_thread=False` because we hop threads via
        # asyncio.to_thread; the asyncio.Lock guards concurrency.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode = WAL;")
        self._conn.execute("PRAGMA synchronous = NORMAL;")
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    @contextmanager
    def _cursor(self) -> Iterator[sqlite3.Cursor]:
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        finally:
            cur.close()

    # ---- language preference --------------------------------------

    async def get_language(self, user_id: int) -> str | None:
        def _run() -> str | None:
            with self._cursor() as cur:
                row = cur.execute(
                    "SELECT language FROM users WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
            return row[0] if row else None

        async with self._lock:
            return await asyncio.to_thread(_run)

    async def set_language(self, user_id: int, language: str) -> None:
        now = int(time.time())

        def _run() -> None:
            with self._cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (user_id, language, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        language = excluded.language,
                        updated_at = excluded.updated_at
                    """,
                    (user_id, language, now, now),
                )

        async with self._lock:
            await asyncio.to_thread(_run)

    # ---- rate limiting --------------------------------------------

    async def check_and_record_rate(
        self, user_id: int, window_seconds: int, max_events: int
    ) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds).

        - Removes events older than `window_seconds`.
        - If under `max_events`, records this event and returns (True, 0).
        - Otherwise returns (False, seconds-until-oldest-rolls-off).
        """
        now = int(time.time())
        cutoff = now - window_seconds

        def _run() -> tuple[bool, int]:
            with self._cursor() as cur:
                cur.execute("DELETE FROM rate_events WHERE ts < ?", (cutoff,))
                row = cur.execute(
                    "SELECT COUNT(*) FROM rate_events WHERE user_id = ? AND ts >= ?",
                    (user_id, cutoff),
                ).fetchone()
                count = int(row[0]) if row else 0
                if count >= max_events:
                    oldest = cur.execute(
                        "SELECT MIN(ts) FROM rate_events WHERE user_id = ? AND ts >= ?",
                        (user_id, cutoff),
                    ).fetchone()
                    oldest_ts = int(oldest[0]) if oldest and oldest[0] is not None else now
                    retry_after = max(1, window_seconds - (now - oldest_ts))
                    return False, retry_after
                cur.execute(
                    "INSERT INTO rate_events (user_id, ts) VALUES (?, ?)",
                    (user_id, now),
                )
                return True, 0

        async with self._lock:
            return await asyncio.to_thread(_run)

    # ---- analysis log (metadata only) -----------------------------

    async def record_analysis(
        self, user_id: int, verdict: str, risk_score: int, duration_ms: int
    ) -> None:
        ts = int(time.time())

        def _run() -> None:
            with self._cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO analyses (user_id, ts, verdict, risk_score, duration_ms)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, ts, verdict, risk_score, duration_ms),
                )

        async with self._lock:
            await asyncio.to_thread(_run)

    async def stats(self) -> dict[str, int]:
        def _run() -> dict[str, int]:
            with self._cursor() as cur:
                total_users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                total_analyses = cur.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
                rows = cur.execute(
                    "SELECT verdict, COUNT(*) FROM analyses GROUP BY verdict"
                ).fetchall()
            stats = {
                "total_users": int(total_users or 0),
                "total_analyses": int(total_analyses or 0),
                "verdict_safe": 0,
                "verdict_suspicious": 0,
                "verdict_phishing": 0,
                "verdict_unknown": 0,
            }
            for verdict, count in rows:
                key = f"verdict_{verdict.lower()}"
                if key in stats:
                    stats[key] = int(count)
            return stats

        async with self._lock:
            return await asyncio.to_thread(_run)

    async def close(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._conn.close)
