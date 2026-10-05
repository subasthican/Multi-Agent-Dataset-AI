"""Explicit input controls; these patterns do not prove general jailbreak safety."""
import json
import re
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _patterns():
    config = json.loads(Path(__file__).with_name("input_filter.json").read_text())
    return {key: [re.compile(p, re.I | re.S) for p in values] for key, values in config.items()}


def sanitize_input(text: str) -> str:
    if any(ord(c) < 32 and c not in "\n\r\t" for c in text):
        raise ValueError("Control characters are not supported in dataset requests.")
    for category, patterns in _patterns().items():
        if any(pattern.search(text) for pattern in patterns):
            if category == "harmful_purpose":
                raise ValueError("Dataset requests facilitating discrimination are not supported.")
            raise ValueError("Provide a dataset requirement without instructions to override the assistant or disclose internal information.")
    return " ".join(text.strip().split())
