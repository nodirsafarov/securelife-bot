"""Tiny i18n helper.

Strings live in `en.py` and `uz.py` as plain dicts. We resolve them by
language code with a fallback to English. Callers pass keyword arguments
which are interpolated via `str.format(**kwargs)`.
"""
from __future__ import annotations

from . import en, uz

LANGUAGES: dict[str, dict[str, str]] = {
    "en": en.MESSAGES,
    "uz": uz.MESSAGES,
}

LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "uz": "O'zbekcha",
}


def t(key: str, lang: str = "en", **kwargs: object) -> str:
    """Translate `key` into `lang`, falling back to English on miss."""
    table = LANGUAGES.get(lang, LANGUAGES["en"])
    template = table.get(key) or LANGUAGES["en"].get(key) or key
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return template
    return template
