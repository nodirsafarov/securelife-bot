"""English UI strings."""
from __future__ import annotations

MESSAGES: dict[str, str] = {
    # ---- onboarding & language ------------------------------------
    "language_choose": "🌐 Please choose your language:\n\nIltimos, tilni tanlang:",
    "language_set": "✅ Language set to English.\n\nSend me any suspicious message, link, or SMS — I'll analyze it for phishing and explain the result in plain English.",
    # ---- /start ---------------------------------------------------
    "start": (
        "👋 *Welcome to {bot_name}!*\n\n"
        "I'm a phishing detector built to keep ordinary people safe from "
        "scams that arrive over SMS, Telegram, email, or WhatsApp.\n\n"
        "*How to use me:*\n"
        "• Forward or paste any message you find suspicious\n"
        "• I'll tell you whether it looks SAFE, SUSPICIOUS, or PHISHING\n"
        "• I'll explain *why* in your language\n\n"
        "*Commands*\n"
        "/help – how the bot works\n"
        "/about – what this bot is\n"
        "/language – change language\n"
        "/privacy – privacy policy\n\n"
        "⚠️ I'm an assistant, not a guarantee. If in doubt, don't click anything and call your bank directly."
    ),
    # ---- /help ----------------------------------------------------
    "help": (
        "*How to use {bot_name}*\n\n"
        "1. Receive a suspicious message anywhere (SMS, Telegram, email).\n"
        "2. Copy the full text or forward it to me.\n"
        "3. I'll analyze it and reply with one of three verdicts:\n"
        "   ✅ *SAFE* — looks legitimate\n"
        "   ⚠️ *SUSPICIOUS* — be careful, verify before acting\n"
        "   🚨 *PHISHING* — strong signs of a scam, do not click\n\n"
        "*Tips for staying safe:*\n"
        "• Banks NEVER ask for full card numbers, CVV, SMS codes, or passwords by message.\n"
        "• Real domains end in the company's official root, e.g. `uzcard.uz` — not `uzcard-bonus.com`.\n"
        "• If a message says \"you won\" or \"urgent action required\", slow down.\n"
        "• When unsure, call the official number printed on your bank card.\n\n"
        "Send any text to start."
    ),
    # ---- /about ---------------------------------------------------
    "about": (
        "*About {bot_name}*\n\n"
        "An open-source Telegram bot that uses AI to detect phishing in "
        "messages, links, SMS, and emails. Designed for users in Uzbekistan "
        "and Central Asia, with awareness of local banks, services, and scam patterns.\n\n"
        "Built by [@nodirsafarov](https://github.com/nodirsafarov).\n"
        "Source code: https://github.com/nodirsafarov/securelife-bot\n\n"
        "_This bot is a tool, not a guarantee. Always verify with the official organization before acting on any message._"
    ),
    # ---- /privacy -------------------------------------------------
    "privacy": (
        "*Privacy*\n\n"
        "• I store your Telegram user ID and language preference only.\n"
        "• I do NOT store the content of messages you send me.\n"
        "• Each message is analyzed and immediately discarded.\n"
        "• I keep aggregate counters (how many analyses, what verdicts) for monitoring.\n"
        "• I do NOT share data with third parties beyond the AI model used to analyze your message.\n\n"
        "Open source: you can audit every line at https://github.com/nodirsafarov/securelife-bot"
    ),
    # ---- /language ------------------------------------------------
    "language_prompt": "🌐 Choose your language:",
    # ---- analysis flow --------------------------------------------
    "analyzing": "🔍 Analyzing your message…",
    "send_text_hint": "Send me any suspicious message, link, or SMS to analyze.",
    "input_too_short": "❌ The message is too short to analyze. Please send the full text.",
    "input_too_long": "❌ The message is too long ({max} characters max). Please shorten it and resend.",
    # ---- verdicts -------------------------------------------------
    "verdict_safe": "✅ *Verdict: SAFE*",
    "verdict_suspicious": "⚠️ *Verdict: SUSPICIOUS*",
    "verdict_phishing": "🚨 *Verdict: PHISHING*",
    "verdict_unknown": "❓ *Verdict: UNCLEAR*",
    "result_template": (
        "{verdict_line}\n"
        "*Risk score:* {risk_score}/100\n\n"
        "*Why:*\n{reasons}\n\n"
        "*What to do:*\n{advice}\n\n"
        "_Disclaimer: this is an AI assessment, not a guarantee. When in doubt, contact the company directly using the number on your card._"
    ),
    # ---- rate limit -----------------------------------------------
    "rate_limited": "⏳ You've hit the hourly limit. Please try again in {minutes} minutes.",
    # ---- errors ---------------------------------------------------
    "error_generic": "😔 Sorry, something went wrong while analyzing. Please try again in a moment.",
    "error_ai_unavailable": "😔 The AI service is temporarily unavailable. Please try again in a few minutes.",
    # ---- /stats (admin only) -------------------------------------
    "stats_title": "*SecureLife stats*",
    "stats_body": (
        "Users: {total_users}\n"
        "Analyses: {total_analyses}\n"
        "✅ Safe: {verdict_safe}\n"
        "⚠️ Suspicious: {verdict_suspicious}\n"
        "🚨 Phishing: {verdict_phishing}"
    ),
    "not_admin": "❌ This command is for administrators only.",
    # ---- buttons --------------------------------------------------
    "btn_english": "🇬🇧 English",
    "btn_uzbek": "🇺🇿 O'zbekcha",
}
