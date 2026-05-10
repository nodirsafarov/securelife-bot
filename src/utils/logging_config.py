"""Logging setup. Privacy-first: never log message content."""
from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with a consistent format.

    Privacy note: handlers in this project must NOT log raw message
    content from users. Only metadata (user_id, verdict, timestamp,
    duration) should be emitted.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(log_level)
    # Reset existing handlers (so reconfiguration in tests is clean).
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)

    # Tame noisy third-party loggers.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("telegram.ext").setLevel(logging.INFO)
    logging.getLogger("google").setLevel(logging.WARNING)
