"""Top-level analyzer that coordinates heuristics + LLM and shapes the response."""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Iterable

from ..i18n import t
from . import heuristics, prompts
from .gemini_client import GeminiClient, GeminiError, GeminiUnavailable


log = logging.getLogger(__name__)


_VALID_VERDICTS = {"SAFE", "SUSPICIOUS", "PHISHING"}


@dataclass(frozen=True)
class AnalysisResult:
    verdict: str
    risk_score: int
    reasons: list[str]
    advice: list[str]
    language: str
    duration_ms: int
    used_fallback: bool


class PhishingDetector:
    def __init__(self, gemini: GeminiClient) -> None:
        self._gemini = gemini

    async def analyze(self, message: str, language: str) -> AnalysisResult:
        start = time.monotonic()
        heuristic = heuristics.analyze(message)
        try:
            llm_result = await self._gemini.analyze(
                system_prompt=prompts.SYSTEM_PROMPT,
                user_prompt=prompts.build_user_prompt(
                    message=message,
                    language=language,
                    heuristics_text=heuristic.to_prompt_context(),
                ),
            )
        except (GeminiUnavailable, GeminiError) as exc:
            log.warning("LLM unavailable, falling back to heuristics: %s", exc)
            return self._heuristic_only_result(heuristic, language, start)

        parsed = llm_result.parsed
        verdict = _normalize_verdict(parsed.get("verdict"))
        risk_score = _clamp_int(parsed.get("risk_score"), 0, 100, default=heuristic.score)
        reasons = _stringify_list(parsed.get("reasons"), max_items=5)
        advice = _stringify_list(parsed.get("advice"), max_items=4)

        if heuristic.score >= 60 and verdict == "SAFE":
            verdict = "SUSPICIOUS"
            risk_score = max(risk_score, heuristic.score)

        if not reasons:
            reasons = self._fallback_reasons(heuristic, language)
        if not advice:
            advice = self._fallback_advice(language)

        duration_ms = int((time.monotonic() - start) * 1000)
        return AnalysisResult(
            verdict=verdict,
            risk_score=risk_score,
            reasons=reasons,
            advice=advice,
            language=language,
            duration_ms=duration_ms,
            used_fallback=False,
        )

    def _heuristic_only_result(
        self, heuristic: heuristics.HeuristicResult, language: str, start: float
    ) -> AnalysisResult:
        verdict = "PHISHING" if heuristic.score >= 60 else "SUSPICIOUS"
        reasons = self._fallback_reasons(heuristic, language)
        advice = self._fallback_advice(language)
        duration_ms = int((time.monotonic() - start) * 1000)
        return AnalysisResult(
            verdict=verdict,
            risk_score=heuristic.score if heuristic.score > 0 else 40,
            reasons=reasons,
            advice=advice,
            language=language,
            duration_ms=duration_ms,
            used_fallback=True,
        )

    @staticmethod
    def _fallback_reasons(h: heuristics.HeuristicResult, lang: str) -> list[str]:
        if lang == "uz":
            r: list[str] = []
            if h.requests_credentials:
                r.append("Karta raqami, CVV, SMS kod yoki parol so'ralmoqda — banklar buni qilmaydi")
            if h.suspicious_urls:
                r.append("Shubhali yoki rasmiy bo'lmagan domen aniqlandi")
            if h.has_urgency:
                r.append("Shoshilinch harakat talab qilinmoqda — keng tarqalgan firibgarlik usuli")
            if h.has_lure:
                r.append("Mukofot yoki yutuq haqida vaʼda — keng tarqalgan firibgarlik usuli")
            if h.has_shortener:
                r.append("URL qisqartiruvchi ishlatilgan — haqiqiy manzil yashirilmoqda")
            if h.has_ip_or_punycode:
                r.append("URL'da IP-manzil yoki punycode mavjud — yuqori darajadagi shubha")
            if not r:
                r.append("Avtomatik tahlil aniq belgilarni topa olmadi — ehtiyot bo'ling")
            return r
        r = []
        if h.requests_credentials:
            r.append("Asks for card number, CVV, OTP or password — banks never do this")
        if h.suspicious_urls:
            r.append("Suspicious or non-official domain detected")
        if h.has_urgency:
            r.append("Urgent action requested — common scam tactic")
        if h.has_lure:
            r.append("Promises a reward or prize — common scam tactic")
        if h.has_shortener:
            r.append("Uses a URL shortener — real destination is hidden")
        if h.has_ip_or_punycode:
            r.append("URL contains an IP address or punycode — high suspicion")
        if not r:
            r.append("Automated analysis found no clear signals — proceed with caution")
        return r

    @staticmethod
    def _fallback_advice(lang: str) -> list[str]:
        if lang == "uz":
            return [
                "Hech qanday linkni bosmang",
                "Karta orqasidagi rasmiy raqamga qo'ng'iroq qiling",
                "Karta ma'lumotlarini, kodlarni yoki parolni hech qachon bermang",
            ]
        return [
            "Do not click any links",
            "Call the official number on the back of your card",
            "Never share card details, codes, or passwords",
        ]


def _normalize_verdict(value: object) -> str:
    if isinstance(value, str):
        upper = value.strip().upper()
        if upper in _VALID_VERDICTS:
            return upper
    return "SUSPICIOUS"


def _clamp_int(value: object, lo: int, hi: int, default: int) -> int:
    try:
        n = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    if n < lo:
        return lo
    if n > hi:
        return hi
    return n


def _stringify_list(value: object, max_items: int) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
        return []
    out: list[str] = []
    for item in value:  # type: ignore[assignment]
        if not isinstance(item, str):
            continue
        s = item.strip()
        if s:
            out.append(s[:280])
        if len(out) >= max_items:
            break
    return out


_MARKDOWN_SPECIAL_RE = re.compile(r"([_*`\[])")


def _escape_markdown(text: str) -> str:
    """Escape Telegram legacy-Markdown special chars in LLM/user-derived text.

    `reasons`/`advice` come from Gemini's free-form output (which often
    echoes fragments of the analyzed message, e.g. URLs with underscores).
    An unbalanced `_`/`*`/`` ` ``/`[` makes Telegram reject the *entire*
    message with "can't parse entities", so the bot would silently fail
    to reply. Legacy Markdown supports backslash-escaping these four.
    """
    return _MARKDOWN_SPECIAL_RE.sub(r"\\\1", text)


def format_result_message(result: AnalysisResult) -> str:
    """Render an AnalysisResult into the localized template for Telegram."""
    if result.verdict == "SAFE":
        verdict_line = t("verdict_safe", lang=result.language)
    elif result.verdict == "SUSPICIOUS":
        verdict_line = t("verdict_suspicious", lang=result.language)
    elif result.verdict == "PHISHING":
        verdict_line = t("verdict_phishing", lang=result.language)
    else:
        verdict_line = t("verdict_unknown", lang=result.language)

    reasons_block = "\n".join(f"• {_escape_markdown(r)}" for r in result.reasons) or "—"
    advice_block = "\n".join(f"• {_escape_markdown(a)}" for a in result.advice) or "—"

    return t(
        "result_template",
        lang=result.language,
        verdict_line=verdict_line,
        risk_score=result.risk_score,
        reasons=reasons_block,
        advice=advice_block,
    )
