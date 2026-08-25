from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field


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


class CatalogDatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    domain: str = Field(..., min_length=1, max_length=100)
    task: str = Field(..., min_length=1, max_length=100)


class CatalogDatasetUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    domain: Optional[str] = Field(default=None, min_length=1, max_length=100)
    task: Optional[str] = Field(default=None, min_length=1, max_length=100)


class CatalogDatasetResponse(BaseModel):
    id: str
    name: str
    description: str
    domain: str
    task: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
