"""Thin async wrapper around google-generativeai with retries.

google-generativeai exposes a synchronous SDK as the most stable surface
across versions; we run it in a worker thread via asyncio.to_thread to
keep the bot's event loop responsive.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass

import google.generativeai as genai
from google.api_core import exceptions as gax_exceptions


log = logging.getLogger(__name__)


class GeminiError(RuntimeError):
    pass


class GeminiUnavailable(GeminiError):
    pass


@dataclass(frozen=True)
class GeminiResult:
    raw_text: str
    parsed: dict


class GeminiClient:
    def __init__(self, api_key: str, model: str, timeout_seconds: int = 30) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")
        genai.configure(api_key=api_key)
        self._model_name = model
        self._timeout = timeout_seconds
        self._model = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "temperature": 0.2,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 1024,
                "response_mime_type": "application/json",
            },
        )

    async def analyze(self, system_prompt: str, user_prompt: str) -> GeminiResult:
        attempts = 3
        backoff = 1.0
        last_exc: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                raw = await asyncio.wait_for(
                    asyncio.to_thread(self._call, system_prompt, user_prompt),
                    timeout=self._timeout,
                )
                parsed = _safe_json_loads(raw)
                if parsed is None:
                    raise GeminiError("Could not parse JSON from model response")
                return GeminiResult(raw_text=raw, parsed=parsed)
            except (gax_exceptions.ResourceExhausted, gax_exceptions.TooManyRequests) as exc:
                last_exc = exc
                log.warning("Gemini rate-limited (attempt %d): %s", attempt, exc)
                await asyncio.sleep(min(backoff, 30))
                backoff *= 3
            except (gax_exceptions.ServiceUnavailable, gax_exceptions.DeadlineExceeded, asyncio.TimeoutError) as exc:
                last_exc = exc
                log.warning("Gemini transient failure (attempt %d): %s", attempt, exc)
                await asyncio.sleep(backoff)
                backoff *= 2
            except Exception as exc:
                log.exception("Unexpected Gemini error: %s", exc)
                raise GeminiError(str(exc)) from exc
        raise GeminiUnavailable(f"Exhausted retries: {last_exc}")

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        response = self._model.generate_content(
            [
                {"role": "user", "parts": [{"text": system_prompt}]},
                {"role": "model", "parts": [{"text": "Understood. I will respond with JSON only."}]},
                {"role": "user", "parts": [{"text": user_prompt}]},
            ]
        )
        if not response or not getattr(response, "text", None):
            raise GeminiError("Empty response from Gemini")
        return response.text


_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(.+?)\s*```", re.DOTALL | re.IGNORECASE)


def _safe_json_loads(text: str) -> dict | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = _FENCED_JSON_RE.search(text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None
