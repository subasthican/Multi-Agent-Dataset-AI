import math
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

from agents.nlp_agent.agent import classify_domain, classify_task

from .huggingface_source import search_huggingface_datasets
from .kaggle_source import KaggleUnavailableError, search_kaggle_datasets
from .openml_source import search_openml_datasets

SOURCE_COUNT = 3
UNSPECIFIED = "unspecified"


def _safe_kaggle_search(query: str, limit: int) -> List[Dict]:
    """Kaggle is the one source that can raise (missing/bad token) rather
    than just return nothing - normalized here to the same best-effort
    empty-list behavior as OpenML/HuggingFace."""
    try:
        return search_kaggle_datasets(query, limit=limit)
    except KaggleUnavailableError:
        return []


def _infer_metadata(item: Dict) -> Dict:
    """None of the three external APIs expose domain/task, so every result
    used to be stuck at "unspecified" and could never earn the Evaluation
    Agent's domain/task match bonus - even a perfect result would lose to a
    mediocre catalog one purely on that structural gap. This reuses the NLP
    Agent's own rule-based classifier (same config.json keyword rules) on
    the result's own description text as a best-effort guess, rather than
    leaving it permanently blank. An unmatched guess falls back to the
    classifier's own default ("general"/"machine_learning") - still no
    bonus, same as before, just no longer worse than trying."""
    if item.get("domain") == UNSPECIFIED:
        item["domain"] = classify_domain(item["description"], [])
    if item.get("task") == UNSPECIFIED:
        item["task"] = classify_task(item["description"], [])
    return item


def collect_external_datasets(query: str, limit: int = 5) -> List[Dict]:
    """Live dataset search across Kaggle, OpenML, and HuggingFace, run
    concurrently (each is an independent network call) and merged into one
    list. Every source is best-effort: an unconfigured/unreachable/rate-
    limited source contributes an empty list rather than failing the whole
    search - callers never need to special-case any one of them.

    `limit` is the total across all three sources (split roughly evenly),
    not a per-source limit, so results stay comparable to the local
    catalog's own result count instead of tripling it.
    """
    per_source_limit = max(1, math.ceil(limit / SOURCE_COUNT))

    with ThreadPoolExecutor(max_workers=SOURCE_COUNT) as executor:
        kaggle_future = executor.submit(_safe_kaggle_search, query, per_source_limit)
        openml_future = executor.submit(search_openml_datasets, query, per_source_limit)
        huggingface_future = executor.submit(search_huggingface_datasets, query, per_source_limit)

        results = kaggle_future.result() + openml_future.result() + huggingface_future.result()

    return [_infer_metadata(item) for item in results]
