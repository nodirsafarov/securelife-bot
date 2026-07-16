"""Lightweight URL extraction and normalization.

We extract URLs so the analyzer can attach them as structured context
when calling the LLM, and so heuristics can flag suspicious domains.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

import tldextract

# Match http(s):// and bare domain.tld[/path] forms.
_URL_RE = re.compile(
    r"""
    \b
    (?:
        https?://[^\s<>"'`]+
      | (?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s<>"'`]*)?
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


@dataclass(frozen=True)
class ExtractedUrl:
    raw: str
    domain: str
    registered_domain: str
    suffix: str
    has_scheme: bool
    has_userinfo: bool


def _has_userinfo(raw: str, has_scheme: bool) -> bool:
    """True if the URL authority contains a `userinfo@` prefix.

    Phishing links abuse this to show a trusted brand before the `@`
    (e.g. `http://uzcard.uz@evil-scam.ru/`) while the browser/parser
    only ever connects to the host after it. tldextract correctly
    ignores the userinfo when resolving registered_domain, so this
    needs its own explicit check against the raw URL.
    """
    if not has_scheme:
        return False
    return "@" in urlsplit(raw).netloc


def extract_urls(text: str) -> list[ExtractedUrl]:
    """Pull every plausible URL out of `text` and decompose each."""
    if not text:
        return []
    seen: set[str] = set()
    results: list[ExtractedUrl] = []
    for match in _URL_RE.finditer(text):
        raw = match.group(0).rstrip(".,;:!?)\"'")
        if raw in seen:
            continue
        seen.add(raw)
        has_scheme = raw.lower().startswith(("http://", "https://"))
        parsed = tldextract.extract(raw)
        domain = ".".join(part for part in [parsed.subdomain, parsed.domain, parsed.suffix] if part)
        registered = parsed.registered_domain or parsed.domain
        if not registered:
            continue
        results.append(
            ExtractedUrl(
                raw=raw,
                domain=domain or raw,
                registered_domain=registered,
                suffix=parsed.suffix,
                has_scheme=has_scheme,
                has_userinfo=_has_userinfo(raw, has_scheme),
            )
        )
    return results
