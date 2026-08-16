from typing import List

from pydantic import BaseModel


class DatasetMatch(BaseModel):
    id: int
    name: str
    domain: str
    task: str
    description: str
    similarity: float


class DiscoveryResult(BaseModel):
    query: str
    matches: List[DatasetMatch]
