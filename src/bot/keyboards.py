"""Inline keyboards for language selection."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..i18n import t


def language_keyboard(current_lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=t("btn_uzbek", lang=current_lang),
                    callback_data="lang:uz",
                ),
                InlineKeyboardButton(
                    text=t("btn_english", lang=current_lang),
                    callback_data="lang:en",
                ),
            ]
        ]
    )
