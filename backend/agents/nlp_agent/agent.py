import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from llm.gemini_client import LLMUnavailableError, generate_response
from llm.prompts import dataset_prompt

from .models import QueryAnalysisResult, QueryInput
from .preprocessing import clean_text, extract_entities, extract_keywords, get_nlp_model

CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULT_DOMAIN = "general"
DEFAULT_TASK = "machine_learning"
DEFAULT_DATA_TYPE = "tabular"

REQUIRED_LLM_FIELDS = {"domain", "task", "keywords", "data_type"}
CODE_FENCE_PATTERN = re.compile(r"^```(?:json)?|```$", re.MULTILINE)


@lru_cache(maxsize=1)
def load_config() -> Dict[str, Dict[str, List[str]]]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def _match_category(text: str, keywords: List[str], categories: Dict[str, List[str]], default: str) -> str:
    """Whole-word/phrase match, not substring. A plain `trigger in haystack`
    check let short triggers match inside unrelated words — e.g. adding an
    "automotive" domain with the trigger "car" would otherwise also fire on
    "scarcity", "healthcare", or "discard". Same bug class already fixed
    once in evaluation_agent/scorer.py's keyword matching; \\b word
    boundaries fix it here too while still matching multi-word triggers
    like "price prediction" or "time series" correctly."""
    haystack = f"{text.lower()} {' '.join(keywords)}"
    for category, triggers in categories.items():
        if any(re.search(rf"\b{re.escape(trigger)}\b", haystack) for trigger in triggers):
            return category
    return default


def classify_domain(text: str, keywords: List[str]) -> str:
    return _match_category(text, keywords, load_config().get("domains", {}), DEFAULT_DOMAIN)


def classify_task(text: str, keywords: List[str]) -> str:
    return _match_category(text, keywords, load_config().get("tasks", {}), DEFAULT_TASK)


def classify_data_type(text: str, keywords: List[str]) -> str:
    return _match_category(text, keywords, load_config().get("data_types", {}), DEFAULT_DATA_TYPE)


def _parse_llm_json(raw_text: str) -> Optional[dict]:
    cleaned = CODE_FENCE_PATTERN.sub("", raw_text.strip()).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or not REQUIRED_LLM_FIELDS.issubset(parsed.keys()):
        return None
    return parsed


def _understand_with_llm(query: str) -> Optional[dict]:
    try:
        raw = generate_response(dataset_prompt(query))
    except LLMUnavailableError:
        return None
    return _parse_llm_json(raw)


def analyze_query(text: str) -> QueryAnalysisResult:
    """Understand a natural-language dataset request.

    Tries the Gemini LLM first for richer domain/task/data-type
    understanding; falls back to the deterministic rule-based classifier
    (config.json) when the LLM is unavailable or returns an unusable
    response, so the agent keeps working without an API key.
    """
    validated = QueryInput(query=text)
    cleaned = clean_text(validated.query)

    doc = get_nlp_model()(cleaned)
    keywords = extract_keywords(doc)
    entities = extract_entities(doc)

    llm_result = _understand_with_llm(cleaned)
    if llm_result is not None:
        llm_keywords = [str(k).lower() for k in (llm_result.get("keywords") or [])]
        merged_keywords = list(dict.fromkeys([*keywords, *llm_keywords]))
        return QueryAnalysisResult(
            original_query=validated.query,
            domain=str(llm_result["domain"]).lower(),
            task=str(llm_result["task"]).lower(),
            data_type=str(llm_result["data_type"]).lower(),
            keywords=merged_keywords,
            entities=entities,
            understanding_source="llm",
        )

    return QueryAnalysisResult(
        original_query=validated.query,
        domain=classify_domain(cleaned, keywords),
        task=classify_task(cleaned, keywords),
        data_type=classify_data_type(cleaned, keywords),
        keywords=keywords,
        entities=entities,
        understanding_source="rule_based",
    )
