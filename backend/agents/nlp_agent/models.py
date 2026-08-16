from typing import Dict, List

from pydantic import BaseModel, Field, field_validator

MAX_QUERY_LENGTH = 300


class QueryInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=MAX_QUERY_LENGTH)

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("query must not be empty")
        return cleaned


class QueryAnalysisResult(BaseModel):
    original_query: str
    domain: str
    task: str
    data_type: str
    keywords: List[str]
    entities: List[Dict[str, str]] = Field(default_factory=list)
    understanding_source: str = "rule_based"
