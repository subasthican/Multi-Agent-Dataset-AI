import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from .models import QueryAnalysisResult, QueryInput
from .preprocessing import clean_text, extract_entities, extract_keywords, get_nlp_model

CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULT_DOMAIN = "general"
DEFAULT_TASK = "machine_learning"
DEFAULT_DATA_TYPE = "tabular"


@lru_cache(maxsize=1)
def load_config() -> Dict[str, Dict[str, List[str]]]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def _match_category(text: str, keywords: List[str], categories: Dict[str, List[str]], default: str) -> str:
    haystack = f"{text.lower()} {' '.join(keywords)}"
    for category, triggers in categories.items():
        if any(trigger in haystack for trigger in triggers):
            return category
    return default


def classify_domain(text: str, keywords: List[str]) -> str:
    return _match_category(text, keywords, load_config().get("domains", {}), DEFAULT_DOMAIN)


def classify_task(text: str, keywords: List[str]) -> str:
    return _match_category(text, keywords, load_config().get("tasks", {}), DEFAULT_TASK)


def classify_data_type(text: str, keywords: List[str]) -> str:
    return _match_category(text, keywords, load_config().get("data_types", {}), DEFAULT_DATA_TYPE)


def analyze_query(text: str) -> QueryAnalysisResult:
    validated = QueryInput(query=text)
    cleaned = clean_text(validated.query)

    doc = get_nlp_model()(cleaned)
    keywords = extract_keywords(doc)
    entities = extract_entities(doc)

    return QueryAnalysisResult(
        original_query=validated.query,
        domain=classify_domain(cleaned, keywords),
        task=classify_task(cleaned, keywords),
        data_type=classify_data_type(cleaned, keywords),
        keywords=keywords,
        entities=entities,
    )
