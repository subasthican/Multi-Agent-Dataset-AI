import os
import hashlib
import math
import re
import time
from functools import lru_cache
from pathlib import Path
from threading import Lock

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Repo-root .env (backend/llm/gemini_client.py -> llm -> backend -> repo root),
# so the key can live in one place alongside the rest of the project's .env.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DEFAULT_MODEL_NAME = "gemini-3.5-flash"


class LLMUnavailableError(Exception):
    """Raised when the LLM cannot be reached (no key, network/API error)."""

    def __init__(self, message: str, *, reason: str = "UNAVAILABLE", retry_after_seconds: int | None = None, provider_attempted: bool = False):
        super().__init__(message)
        self.reason = reason
        self.retry_after_seconds = retry_after_seconds
        self.provider_attempted = provider_attempted


_cooldowns: dict[tuple[str, str], tuple[float, str]] = {}
_cooldown_lock = Lock()


def _provider_cooldown(exc: Exception) -> tuple[str, int] | None:
    """Use structured SDK quota details; never infer a successful model result."""
    code = getattr(exc, "code", None)
    if code not in {429, 503}:
        return None
    payload = getattr(exc, "details", {})
    error = payload.get("error", payload) if isinstance(payload, dict) else {}
    details = error.get("details", []) if isinstance(error, dict) else []
    daily = False
    delay = 60
    provider_delay = False
    for detail in details if isinstance(details, list) else []:
        if not isinstance(detail, dict):
            continue
        violations = detail.get("violations", [])
        for violation in violations if isinstance(violations, list) else []:
            if isinstance(violation, dict) and "perday" in str(violation.get("quotaId", "")).lower():
                daily = True
        retry = str(detail.get("retryDelay", ""))
        if re.fullmatch(r"\d+(?:\.\d+)?s", retry):
            delay = max(1, math.ceil(float(retry[:-1])))
            provider_delay = True
    if daily and not provider_delay:
        # No reset information: allow a new probe after one hour. This
        # backoff is not a promise that the daily quota will then reset.
        delay = 3600
    return ("DAILY_QUOTA" if daily else "RATE_LIMIT" if code == 429 else "TEMPORARY_UNAVAILABLE", delay)


def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMUnavailableError("GEMINI_API_KEY is not set")
    return _client_for_key(api_key)


@lru_cache(maxsize=1)
def _client_for_key(api_key: str) -> genai.Client:
    # A failed request should reach the fallback promptly. The SDK otherwise
    # retries up to five times before our quota/service cooldown can start.
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(
        timeout=30_000, retry_options=types.HttpRetryOptions(attempts=1),
    ))


def generate_response(prompt: str) -> str:
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL_NAME)
    key_fingerprint = hashlib.sha256(os.getenv("GEMINI_API_KEY", "").encode()).hexdigest()
    scope = (key_fingerprint, model_name)
    with _cooldown_lock:
        cooldown = _cooldowns.get(scope)
        if cooldown and cooldown[0] > time.monotonic():
            remaining = max(1, math.ceil(cooldown[0] - time.monotonic()))
            raise LLMUnavailableError(
                f"Gemini {cooldown[1].lower()} cooldown; retry in {remaining} seconds. Using rule-based understanding.",
                reason=cooldown[1], retry_after_seconds=remaining,
            )
        _cooldowns.pop(scope, None)
    provider_attempted = False
    try:
        client = get_client()
        provider_attempted = True
        response = client.models.generate_content(model=model_name, contents=prompt)
    except LLMUnavailableError:
        raise
    except Exception as exc:  # network/API errors from the SDK
        cooldown = _provider_cooldown(exc)
        if cooldown:
            reason, delay = cooldown
            with _cooldown_lock:
                _cooldowns[scope] = (time.monotonic() + delay, reason)
            raise LLMUnavailableError(str(exc), reason=reason, retry_after_seconds=delay, provider_attempted=provider_attempted) from exc
        raise LLMUnavailableError(str(exc), provider_attempted=provider_attempted) from exc

    if not response.text:
        raise LLMUnavailableError("empty response from LLM", provider_attempted=True)
    return response.text
