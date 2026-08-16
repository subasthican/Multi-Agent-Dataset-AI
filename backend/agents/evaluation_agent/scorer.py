from agents.discovery_agent.models import DatasetMatch
from agents.nlp_agent.models import QueryAnalysisResult

SIMILARITY_WEIGHT = 50
DOMAIN_MATCH_WEIGHT = 25
TASK_MATCH_WEIGHT = 15
KEYWORD_MATCH_WEIGHT_PER_HIT = 2
KEYWORD_MATCH_MAX = 10


def calculate_score(dataset: DatasetMatch, requirement: QueryAnalysisResult) -> float:
    score = dataset.similarity * SIMILARITY_WEIGHT

    if dataset.domain.lower() == requirement.domain.lower():
        score += DOMAIN_MATCH_WEIGHT

    if dataset.task.lower() == requirement.task.lower():
        score += TASK_MATCH_WEIGHT

    description = dataset.description.lower()
    keyword_hits = sum(1 for keyword in requirement.keywords if keyword.lower() in description)
    score += min(keyword_hits * KEYWORD_MATCH_WEIGHT_PER_HIT, KEYWORD_MATCH_MAX)

    return round(min(score, 100), 2)
