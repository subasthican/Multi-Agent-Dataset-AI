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
    # A real, clickable link to the dataset's actual page on its source
    # platform (Kaggle/OpenML/HuggingFace) or None for a catalog entry with
    # no admin-provided reference — never fabricated for a source that
    # doesn't have one, so a link is only ever shown when it's real.
    url: Optional[str] = None


class DiscoveryResult(BaseModel):
    query: str
    matches: List[DatasetMatch]


class CatalogDatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    domain: str = Field(..., min_length=1, max_length=100)
    task: str = Field(..., min_length=1, max_length=100)
    # Optional — curated catalog entries are hand-written and don't
    # inherently correspond to a real page anywhere, unlike a live Kaggle/
    # OpenML/HuggingFace result. An admin can attach one if the entry does
    # represent a specific real dataset they have a link for.
    url: Optional[str] = Field(default=None, max_length=500)


class CatalogDatasetUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    domain: Optional[str] = Field(default=None, min_length=1, max_length=100)
    task: Optional[str] = Field(default=None, min_length=1, max_length=100)
    url: Optional[str] = Field(default=None, max_length=500)


class CatalogDatasetResponse(BaseModel):
    id: str
    name: str
    description: str
    domain: str
    task: str
    url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
