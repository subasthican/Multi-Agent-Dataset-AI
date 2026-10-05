"""Minimize contact identifiers before storage or provider submission.

Pattern redaction is a limited safeguard, not comprehensive PII detection.
"""
import re

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ().-]{7,}\d)(?!\w)")


def redact_sensitive_text(text: str) -> str:
    return PHONE.sub("[REDACTED_PHONE]", EMAIL.sub("[REDACTED_EMAIL]", text))
