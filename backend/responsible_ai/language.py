"""Conservative English-language disclosure for the current fallback models."""
import re
from langdetect import DetectorFactory, detect_langs, LangDetectException

DetectorFactory.seed = 0


def supported_english(text: str) -> bool:
    # Very short technical phrases have unreliable language classification.
    # Permit them; longer unsupported-language requests must be explicit.
    words = set(re.findall(r"\w+", text.lower()))
    # Short English technical requests can be confidently misdetected. Explicit
    # English request phrasing is a stronger signal than a short-text score.
    if words.intersection({"find", "need", "looking", "please"}) and words.intersection({"for", "to", "the", "datasets"}):
        return True
    if len(re.findall(r"\w+", text)) < 4:
        return True
    try:
        languages = detect_langs(text)
    except LangDetectException:
        return False
    return languages[0].lang == "en" or languages[0].prob < 0.85
