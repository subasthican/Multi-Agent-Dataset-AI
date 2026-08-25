from typing import List

from agents.discovery_agent.models import DatasetMatch
from agents.nlp_agent.models import QueryAnalysisResult

from .models import EvaluatedDataset
from .scorer import calculate_score


def generate_explanation(dataset: DatasetMatch, requirement: QueryAnalysisResult, score: float) -> str:
    reasons = []
    if dataset.domain.lower() == requirement.domain.lower():
        reasons.append(f"matches the {requirement.domain} domain")
    if dataset.task.lower() == requirement.task.lower():
        reasons.append(f"matches the {requirement.task} task")
    if not reasons:
        reasons.append("is semantically related to the request")

    return f"{dataset.name} is recommended because it {' and '.join(reasons)}, with a relevance score of {score}%."


def evaluate_datasets(datasets: List[DatasetMatch], requirement: QueryAnalysisResult) -> List[EvaluatedDataset]:
    evaluated = []
    for dataset in datasets:
        score = calculate_score(dataset, requirement)
        evaluated.append(
            EvaluatedDataset(
                dataset=dataset,
                score=score,
                explanation=generate_explanation(dataset, requirement, score),
            )
        )

    evaluated.sort(key=lambda item: item.score, reverse=True)
    return evaluated
