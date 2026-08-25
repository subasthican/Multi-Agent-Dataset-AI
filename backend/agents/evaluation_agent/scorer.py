import re

from agents.discovery_agent.models import DatasetMatch
from agents.nlp_agent.models import QueryAnalysisResult

SIMILARITY_WEIGHT = 50
DOMAIN_MATCH_WEIGHT = 25
TASK_MATCH_WEIGHT = 15
KEYWORD_MATCH_WEIGHT_PER_HIT = 2
KEYWORD_MATCH_MAX = 10


def _contains_keyword(description: str, keyword: str) -> bool:
    """Whole-word match, not substring. A plain `keyword in description`
    check (the original implementation) matched "age" inside "usage",
    "art" inside "start", etc. - demonstrated live: a Customer Churn
    dataset scored a false keyword hit against the unrelated keyword "age"
    purely because its description contains "usage". \\b word boundaries
    fix that while still matching multi-word phrases correctly."""
    return re.search(rf"\b{re.escape(keyword)}\b", description) is not None


def calculate_score(dataset: DatasetMatch, requirement: QueryAnalysisResult) -> float:
    score = dataset.similarity * SIMILARITY_WEIGHT

    if dataset.domain.lower() == requirement.domain.lower():
        score += DOMAIN_MATCH_WEIGHT

    if dataset.task.lower() == requirement.task.lower():
        score += TASK_MATCH_WEIGHT

    description = dataset.description.lower()
    keyword_hits = sum(1 for keyword in requirement.keywords if _contains_keyword(description, keyword.lower()))
    score += min(keyword_hits * KEYWORD_MATCH_WEIGHT_PER_HIT, KEYWORD_MATCH_MAX)

    return round(min(score, 100), 2)
