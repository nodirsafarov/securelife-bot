"""Entry point: wires everything together and runs the bot via long-polling."""
from __future__ import annotations

import asyncio
import logging
import signal

from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from .analyzer.gemini_client import GeminiClient
from .analyzer.phishing_detector import PhishingDetector
from .bot.handlers import Handlers
from .config import Config
from .storage.db import Database
from .utils.logging_config import setup_logging


log = logging.getLogger(__name__)


_BOT_COMMANDS_EN = [
    BotCommand("start", "Start the bot"),
    BotCommand("help", "How to use the bot"),
    BotCommand("about", "About this bot"),
    BotCommand("privacy", "Privacy policy"),
    BotCommand("language", "Change language"),
]


def _redact_proxy(url: str) -> str:
    if "@" not in url:
        return url
    scheme_split = url.split("://", 1)
    if len(scheme_split) != 2:
        return url
    scheme, rest = scheme_split
    if "@" not in rest:
        return url
    _, host_part = rest.rsplit("@", 1)
    return f"{scheme}://***:***@{host_part}"


async def _post_init(application) -> None:  # type: ignore[no-untyped-def]
    try:
        await application.bot.set_my_commands(_BOT_COMMANDS_EN)
    except Exception:
        log.warning("Could not set bot commands", exc_info=True)


def build_application(config: Config) -> "object":  # type: ignore[empty-body]
    db = Database(config.db_path)
    gemini = GeminiClient(api_key=config.gemini_api_key, model=config.gemini_model)
    detector = PhishingDetector(gemini=gemini)
    handlers = Handlers(config=config, db=db, detector=detector)

    builder = (
        ApplicationBuilder()
        .token(config.telegram_token)
        .post_init(_post_init)
        .concurrent_updates(True)
    )
    if config.telegram_proxy:
        log.info("Using proxy for Telegram API: %s", _redact_proxy(config.telegram_proxy))
        builder = builder.proxy(config.telegram_proxy).get_updates_proxy(config.telegram_proxy)
    app = builder.build()

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help_cmd))
    app.add_handler(CommandHandler("about", handlers.about_cmd))
    app.add_handler(CommandHandler("privacy", handlers.privacy_cmd))
    app.add_handler(CommandHandler("language", handlers.language_cmd))
    app.add_handler(CommandHandler("stats", handlers.stats_cmd))
    app.add_handler(CallbackQueryHandler(handlers.language_callback, pattern=r"^lang:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.message))
    app.add_error_handler(handlers.error_handler)

    app.bot_data["db"] = db
    return app


def main() -> None:
    config = Config.from_env()
    setup_logging(config.log_level)
    log.info(
        "Starting %s (@%s) — model=%s default_lang=%s rate_limit=%d/h",
        config.bot_name,
        config.bot_username,
        config.gemini_model,
        config.default_language,
        config.rate_limit_per_hour,
    )

    app = build_application(config)

    try:
        app.run_polling(  # type: ignore[attr-defined]
            allowed_updates=["message", "edited_message", "callback_query"],
            stop_signals=(signal.SIGINT, signal.SIGTERM),
        )
    finally:
        db = app.bot_data.get("db")  # type: ignore[attr-defined]
        if db is not None:
            try:
                asyncio.run(db.close())
            except Exception:
                pass


if __name__ == "__main__":
    main()
