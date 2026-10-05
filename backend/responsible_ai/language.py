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
    request_words = {"find", "need", "looking", "please", "estimate", "forecast", "predict", "classify", "detect"}
    if words.intersection(request_words) and words.intersection({"for", "to", "the", "datasets", "from", "using", "with"}):
        return True
    # Noun-only technical requests (e.g. "student image data for computer
    # vision") are often misclassified despite several English terms. Require
    # both an English connector and multiple technical words; a single shared
    # loanword such as "diabetes" is not sufficient evidence.
    technical = {"student", "image", "images", "data", "dataset", "datasets", "computer", "vision",
                 "medical", "records", "financial", "classification", "forecasting", "regression",
                 "customer", "weather", "pollution", "property", "housing", "clinical"}
    if words.intersection({"for", "from", "using", "with", "the"}) and len(words & technical) >= 3:
        return True
    if len(re.findall(r"\w+", text)) < 4:
        return True
    try:
        languages = detect_langs(text)
    except LangDetectException:
        return False
    return languages[0].lang == "en" or languages[0].prob < 0.85
