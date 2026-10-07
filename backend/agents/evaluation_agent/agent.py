from typing import List

from agents.discovery_agent.models import DatasetMatch
from agents.nlp_agent.models import QueryAnalysisResult

from .models import EvaluatedDataset
from .scorer import calculate_score
from .topics import matches_topic

# Below this, a result is domain/task-mismatched noise being shown only to
# pad the list out to k, not a genuine match — e.g. a "car types" search
# returning a Diabetes Prediction Dataset at 34% (task-only match, no domain
# or keyword overlap). Previously there was no floor at all: the system
# always filled the quota with whatever scored highest, however irrelevant.
# Calibrated against real evaluated scores: a real domain-or-task match with
# decent similarity clears 45-60+; a pure coincidental-similarity result
# with no domain/task/keyword signal tends to land in the 20s-30s.
MIN_RELEVANCE_SCORE = 40.0


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
    if requirement.warnings or requirement.needs_task_selection:
        return []
    evaluated = []
    for dataset in datasets:
        if not matches_topic(dataset, requirement):
            continue
        if dataset.task != requirement.task:
            continue
        if dataset.source != "catalog" and (not dataset.url or not dataset.license or dataset.task == "machine_learning" or not dataset.metadata_verified):
            continue
        if dataset.source != "catalog" and dataset.license.strip().lower() in {"unknown", "unspecified", "other"}:
            continue
        # Unknown modality is not evidence of suitability for non-tabular use.
        if dataset.data_type != requirement.data_type:
            continue
        score = calculate_score(dataset, requirement)
        evaluated.append(
            EvaluatedDataset(
                dataset=dataset,
                score=score,
                explanation=generate_explanation(dataset, requirement, score),
            )
        )

    evaluated.sort(key=lambda item: item.score, reverse=True)
    # Below the floor is dropped outright rather than kept to pad the list —
    # the frontend already handles an empty result set ("No matching
    # datasets found — try rephrasing"), which is a more honest outcome than
    # confidently presenting an unrelated dataset as a recommendation.
    return [item for item in evaluated if item.score >= MIN_RELEVANCE_SCORE]
