from typing import List, Union

from pydantic import BaseModel


class DatasetMatch(BaseModel):
    id: Union[int, str]
    name: str
    domain: str
    task: str
    description: str
    similarity: float
    source: str = "catalog"


class DiscoveryResult(BaseModel):
    query: str
    matches: List[DatasetMatch]
