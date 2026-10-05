from datetime import datetime
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class DatasetMatch(BaseModel):
    id: Union[int, str]
    name: str
    domain: str
    task: str
    description: str
    similarity: float
    source: str = "catalog"
    data_type: Optional[Literal["tabular", "image", "text", "time_series"]] = None
    # A real, clickable link to the dataset's actual page on its source
    # platform (Kaggle/OpenML/HuggingFace) or None for a catalog entry with
    # no admin-provided reference — never fabricated for a source that
    # doesn't have one, so a link is only ever shown when it's real.
    url: Optional[str] = None


class DiscoveryResult(BaseModel):
    query: str
    matches: List[DatasetMatch]


class CatalogDatasetCreate(BaseModel):
    @field_validator("url")
    @classmethod
    def safe_url(cls, value):
        if value is not None:
            from urllib.parse import urlparse
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("Source URL must be an absolute HTTP(S) URL")
        return value

    data_type: Optional[Literal["tabular", "image", "text", "time_series"]] = None
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
    @field_validator("url")
    @classmethod
    def safe_url(cls, value):
        return CatalogDatasetCreate.safe_url(value)

    @field_validator("name", "description", "domain", "task")
    @classmethod
    def required_fields_not_null(cls, value):
        if value is None or not value.strip():
            raise ValueError("Required catalog fields cannot be null or blank")
        return value.strip()

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    domain: Optional[str] = Field(default=None, min_length=1, max_length=100)
    task: Optional[str] = Field(default=None, min_length=1, max_length=100)
    url: Optional[str] = Field(default=None, max_length=500)
    data_type: Optional[Literal["tabular", "image", "text", "time_series"]] = None


class CatalogDatasetResponse(BaseModel):
    id: str
    name: str
    description: str
    domain: str
    task: str
    data_type: Optional[str]
    url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
