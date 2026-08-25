from typing import List

from pydantic import BaseModel

from agents.evaluation_agent.models import EvaluatedDataset


class SearchHistoryEntry(BaseModel):
    query: str
    domain: str
    task: str
    created_at: str


class RecommendationResponse(BaseModel):
    based_on_domain: str | None
    based_on_task: str | None
    search_count: int
    recommendations: List[EvaluatedDataset]
