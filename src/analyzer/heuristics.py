"""Fast regex-based pre-checks executed before the LLM call.

Heuristics are not authoritative — they only contribute hints to the
prompt. The LLM remains the final judge.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..utils.url_extractor import ExtractedUrl, extract_urls


_UZ_BANK_BRANDS = {
    "uzcard", "humo", "kapitalbank", "hamkorbank", "asakabank",
    "asaka", "nbu", "anorbank", "anor", "ipotekabank", "ipoteka",
    "davrbank", "davr", "tbcbank", "apexbank", "apex", "click",
    "payme", "paynet", "ucell", "beeline", "uztelecom",
}

_UZ_GOV_DOMAINS = {
    "gov.uz", "my.gov.uz", "soliq.uz", "salym.uz", "e-imzo.uz",
    "uzbekiston.uz", "lex.uz",
}

_UZ_DELIVERY_BRANDS = {
    "pochta", "yandex", "wildberries", "ozon", "uzbekistonpochtasi",
    "fedex", "dhl",
}

_URGENT_KEYWORDS_RE = re.compile(
    r"\b(urgent(ly)?|immediate(ly)?|asap|expire(d|s)?|"
    r"suspend(ed)?|lock(ed)?|"
    r"shoshilinch|tezkor|tezda|muddati|bloklan(adi|gan)|to[‘']xtatil(adi|gan)|"
    r"yopil(adi|gan)|cheklan(adi|gan))\b",
    re.IGNORECASE,
)

_LURE_KEYWORDS_RE = re.compile(
    r"\b(won|prize|winner|reward|lottery|gift|free|cashback|bonus|"
    r"yutdin(giz|gan)|sovrin|sovg[‘']a|bonus|mukofot|tabriklaymiz)\b",
    re.IGNORECASE,
)

_CRED_REQUEST_RE = re.compile(
    r"(card[\s-]*number|cvv|otp|sms[\s-]*code|password|pin|"
    r"karta\s*raqam|sms\s*kod|parol|kod yuboring|tasdiqlash kodi)",
    re.IGNORECASE,
)

_OBFUSCATED_DOMAIN_RE = re.compile(
    r"(?:\d{1,3}\.){3}\d{1,3}|xn--[a-z0-9-]+",
    re.IGNORECASE,
)

_SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "is.gd", "buff.ly",
    "rb.gy", "cutt.ly", "rebrand.ly", "shorturl.at", "ow.ly",
}


@dataclass(frozen=True)
class HeuristicResult:
    suspicious_urls: list[ExtractedUrl]
    impersonated_brands: list[str]
    has_urgency: bool
    has_lure: bool
    requests_credentials: bool
    has_shortener: bool
    has_ip_or_punycode: bool
    has_userinfo_trick: bool
    score: int

    def to_prompt_context(self) -> str:
        lines: list[str] = []
        if self.impersonated_brands:
            lines.append(f"- Brands referenced: {', '.join(self.impersonated_brands)}")
        if self.suspicious_urls:
            url_summary = ", ".join(u.registered_domain for u in self.suspicious_urls)
            lines.append(f"- URLs found: {url_summary}")
        if self.has_userinfo_trick:
            lines.append(
                "- URL uses the `trusted-name@real-host` trick (text before the @ "
                "is decorative; the browser only connects to what's after it) — "
                "near-certain phishing signal"
            )
        if self.has_urgency:
            lines.append("- Urgency/pressure language detected")
        if self.has_lure:
            lines.append("- Reward/prize/giveaway language detected")
        if self.requests_credentials:
            lines.append("- Asks for credentials (card number, CVV, OTP, password)")
        if self.has_shortener:
            lines.append("- Uses URL shortener")
        if self.has_ip_or_punycode:
            lines.append("- Uses IP address or punycode in URL (high suspicion)")
        if not lines:
            lines.append("- No obvious heuristic flags")
        return "\n".join(lines)


def _detect_brands(text_lower: str) -> list[str]:
    found: list[str] = []
    for brand in _UZ_BANK_BRANDS | _UZ_DELIVERY_BRANDS:
        if brand in text_lower:
            found.append(brand)
    return sorted(set(found))


def _is_suspicious_url(url: ExtractedUrl) -> bool:
    if url.has_userinfo:
        return True
    if url.registered_domain.lower() in _SHORTENER_DOMAINS:
        return True
    if _OBFUSCATED_DOMAIN_RE.fullmatch(url.registered_domain or ""):
        return True
    domain_lower = url.registered_domain.lower()
    for brand in _UZ_BANK_BRANDS:
        if brand in domain_lower and not domain_lower.endswith(f"{brand}.uz"):
            return True
    for gov in _UZ_GOV_DOMAINS:
        if gov.replace(".", "") in domain_lower.replace(".", "") and not domain_lower.endswith(gov):
            return True
    return False


def analyze(text: str) -> HeuristicResult:
    """Run all regex checks against `text` and return a structured result."""
    text_lower = text.lower()
    urls = extract_urls(text)

    suspicious_urls = [u for u in urls if _is_suspicious_url(u)]
    impersonated = _detect_brands(text_lower)
    has_urgency = bool(_URGENT_KEYWORDS_RE.search(text))
    has_lure = bool(_LURE_KEYWORDS_RE.search(text))
    requests_creds = bool(_CRED_REQUEST_RE.search(text))
    has_shortener = any(u.registered_domain.lower() in _SHORTENER_DOMAINS for u in urls)
    has_ip = any(_OBFUSCATED_DOMAIN_RE.fullmatch(u.registered_domain or "") for u in urls)
    has_userinfo_trick = any(u.has_userinfo for u in urls)

    score = 0
    if suspicious_urls:
        score += 30
    if requests_creds:
        score += 30
    if requests_creds and (has_urgency or has_lure):
        score += 15
    if has_urgency and has_lure:
        score += 20
    elif has_urgency or has_lure:
        score += 10
    if has_shortener:
        score += 10
    if has_ip:
        score += 15
    if has_userinfo_trick:
        score += 25
    if impersonated and not any(b in (u.registered_domain.lower() if u else "") for u in urls for b in impersonated):
        score += 10
    score = min(score, 100)

    return HeuristicResult(
        suspicious_urls=suspicious_urls,
        impersonated_brands=impersonated,
        has_urgency=has_urgency,
        has_lure=has_lure,
        requests_credentials=requests_creds,
        has_shortener=has_shortener,
        has_ip_or_punycode=has_ip,
        has_userinfo_trick=has_userinfo_trick,
        score=score,
    )
