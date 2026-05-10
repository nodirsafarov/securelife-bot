"""Telegram command and message handlers."""
from __future__ import annotations

import logging
from typing import Final

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from ..analyzer.phishing_detector import PhishingDetector, format_result_message
from ..config import Config
from ..i18n import t
from ..storage.db import Database
from .keyboards import language_keyboard


log = logging.getLogger(__name__)

MIN_INPUT_LENGTH: Final[int] = 10
RATE_WINDOW_SECONDS: Final[int] = 3600


class Handlers:
    def __init__(self, config: Config, db: Database, detector: PhishingDetector) -> None:
        self._cfg = config
        self._db = db
        self._detector = detector

    async def _resolve_language(self, user_id: int) -> str:
        stored = await self._db.get_language(user_id)
        return stored or self._cfg.default_language

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return
        user_id = update.effective_user.id
        existing = await self._db.get_language(user_id)
        if existing is None:
            await update.message.reply_text(
                t("language_choose", lang="en"),
                reply_markup=language_keyboard("en"),
            )
            return
        await update.message.reply_text(
            t("start", lang=existing, bot_name=self._cfg.bot_name),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return
        lang = await self._resolve_language(update.effective_user.id)
        await update.message.reply_text(
            t("help", lang=lang, bot_name=self._cfg.bot_name),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

    async def about_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return
        lang = await self._resolve_language(update.effective_user.id)
        await update.message.reply_text(
            t("about", lang=lang, bot_name=self._cfg.bot_name),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

    async def privacy_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return
        lang = await self._resolve_language(update.effective_user.id)
        await update.message.reply_text(
            t("privacy", lang=lang),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

    async def language_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return
        lang = await self._resolve_language(update.effective_user.id)
        await update.message.reply_text(
            t("language_prompt", lang=lang),
            reply_markup=language_keyboard(lang),
        )

    async def language_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query or not query.data or not query.from_user:
            return
        await query.answer()
        choice = query.data.split(":", 1)[1] if ":" in query.data else ""
        if choice not in ("en", "uz"):
            return
        await self._db.set_language(query.from_user.id, choice)
        try:
            await query.edit_message_text(t("language_set", lang=choice))
        except Exception:
            log.debug("Could not edit language-selection message", exc_info=True)
        if query.message:
            await query.message.reply_text(
                t("start", lang=choice, bot_name=self._cfg.bot_name),
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

    async def stats_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return
        user_id = update.effective_user.id
        lang = await self._resolve_language(user_id)
        if user_id not in self._cfg.admin_user_ids:
            await update.message.reply_text(t("not_admin", lang=lang))
            return
        stats = await self._db.stats()
        body = t("stats_title", lang=lang) + "\n\n" + t("stats_body", lang=lang, **stats)
        await update.message.reply_text(body, parse_mode=ParseMode.MARKDOWN)

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.message or update.edited_message
        if not msg or not update.effective_user:
            return

        text = (msg.text or msg.caption or "").strip()
        user_id = update.effective_user.id
        lang = await self._resolve_language(user_id)

        if len(text) < MIN_INPUT_LENGTH:
            await msg.reply_text(t("input_too_short", lang=lang))
            return
        if len(text) > self._cfg.max_input_length:
            await msg.reply_text(
                t("input_too_long", lang=lang, max=self._cfg.max_input_length)
            )
            return

        allowed, retry_after = await self._db.check_and_record_rate(
            user_id=user_id,
            window_seconds=RATE_WINDOW_SECONDS,
            max_events=self._cfg.rate_limit_per_hour,
        )
        if not allowed:
            minutes = max(1, retry_after // 60)
            await msg.reply_text(t("rate_limited", lang=lang, minutes=minutes))
            return

        try:
            await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        except Exception:
            pass

        try:
            result = await self._detector.analyze(message=text, language=lang)
        except Exception as exc:
            log.exception("Analyzer failed for user %s: %s", user_id, exc)
            await msg.reply_text(t("error_generic", lang=lang))
            return

        await self._db.record_analysis(
            user_id=user_id,
            verdict=result.verdict,
            risk_score=result.risk_score,
            duration_ms=result.duration_ms,
        )

        log.info(
            "analysis user=%s verdict=%s score=%d duration_ms=%d fallback=%s lang=%s",
            user_id,
            result.verdict,
            result.risk_score,
            result.duration_ms,
            result.used_fallback,
            lang,
        )

        await msg.reply_text(
            format_result_message(result),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        log.exception("Unhandled exception in handler", exc_info=context.error)
