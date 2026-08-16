from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError

from agents.discovery_agent.agent import search_datasets
from agents.discovery_agent.models import DiscoveryResult
from agents.evaluation_agent.agent import evaluate_datasets
from agents.evaluation_agent.models import EvaluatedDataset
from agents.nlp_agent.agent import analyze_query
from agents.nlp_agent.models import QueryAnalysisResult

app = FastAPI(title="Dataset AI Agent System")

DEFAULT_RESULT_COUNT = 3


class DiscoverResponse(BaseModel):
    understanding: QueryAnalysisResult
    recommendations: List[EvaluatedDataset]


def _discovery_query(understanding: QueryAnalysisResult) -> str:
    return " ".join([understanding.domain, understanding.task, *understanding.keywords])


@app.get("/")
def home():
    return {"message": "Multi Agent Dataset Recommendation System"}


@app.post("/nlp-agent", response_model=QueryAnalysisResult)
def nlp_agent(query: str):
    try:
        return analyze_query(query)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


@app.post("/discovery-agent", response_model=DiscoveryResult)
def discovery_agent(query: str, k: int = DEFAULT_RESULT_COUNT):
    return search_datasets(query, k=k)


@app.post("/evaluation-agent", response_model=List[EvaluatedDataset])
def evaluation_agent(query: str, k: int = DEFAULT_RESULT_COUNT):
    try:
        understanding = analyze_query(query)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc

    discovery_result = search_datasets(_discovery_query(understanding), k=k)
    return evaluate_datasets(discovery_result.matches, understanding)


@app.post("/discover", response_model=DiscoverResponse)
def discover(query: str, k: int = DEFAULT_RESULT_COUNT):
    """Full pipeline: NLP Agent -> Discovery Agent -> Evaluation Agent."""
    try:
        understanding = analyze_query(query)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc

    discovery_result = search_datasets(_discovery_query(understanding), k=k)
    recommendations = evaluate_datasets(discovery_result.matches, understanding)

    return DiscoverResponse(understanding=understanding, recommendations=recommendations)
