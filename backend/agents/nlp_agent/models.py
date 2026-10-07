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
    warnings: List[str] = Field(default_factory=list)
    needs_task_selection: bool = False


# Validate model output before coercion or downstream retrieval.
from typing import Annotated, Literal
from pydantic import ConfigDict, StrictStr

Keyword = Annotated[StrictStr, Field(min_length=1, max_length=60)]


class LLMIntent(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    domain: Literal["healthcare", "finance", "education", "business", "environment", "automotive", "general"]
    task: Literal["classification", "regression", "clustering", "nlp", "computer_vision", "machine_learning"]
    data_type: Literal["tabular", "image", "text", "time_series"]
    keywords: List[Keyword] = Field(max_length=20)
