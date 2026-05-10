"""Lightweight URL extraction and normalization.

We extract URLs so the analyzer can attach them as structured context
when calling the LLM, and so heuristics can flag suspicious domains.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

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
            )
        )
    return results
