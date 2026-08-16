from pydantic import BaseModel

from agents.discovery_agent.models import DatasetMatch


class EvaluatedDataset(BaseModel):
    dataset: DatasetMatch
    score: float
    explanation: str
