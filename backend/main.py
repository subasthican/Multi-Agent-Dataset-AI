import os
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from agents.dataset_collection_agent.agent import collect_external_datasets
from agents.discovery_agent.agent import search_datasets
from agents.discovery_agent.models import DatasetMatch, DiscoveryResult
from agents.evaluation_agent.agent import evaluate_datasets
from agents.evaluation_agent.models import EvaluatedDataset
from agents.nlp_agent.agent import analyze_query
from agents.nlp_agent.models import QueryAnalysisResult
from agents.recommendation_agent.agent import clear_history, get_recommendations, record_search
from agents.recommendation_agent.models import RecommendationResponse
from security.authentication import get_current_user, get_current_user_optional
from security.db import get_db, init_db
from security.db_models import User
from security.router import router as auth_router

app = FastAPI(title="Dataset AI Agent System")

DEFAULT_ALLOWED_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"
allowed_origins = os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.on_event("startup")
def on_startup():
    init_db()

DEFAULT_RESULT_COUNT = 3

# Terms too generic to help either search, and that flood Kaggle's search with
# noise now that it's not just feeding an embedding.
GENERIC_KEYWORDS = {"dataset", "datasets", "data", "machine", "learning", "predicting", "prediction"}
MAX_KAGGLE_KEYWORDS = 2


class DiscoverResponse(BaseModel):
    understanding: QueryAnalysisResult
    recommendations: List[EvaluatedDataset]


def _discovery_query(understanding: QueryAnalysisResult) -> str:
    """Query for the FAISS-embedded catalog search — embeddings handle a
    longer, denser bag of terms fine."""
    return " ".join([understanding.domain, understanding.task, *understanding.keywords])


def _kaggle_query(understanding: QueryAnalysisResult) -> str:
    """Query for Kaggle's own search endpoint, which — unlike FAISS similarity
    — returns zero results for long multi-keyword strings, so this stays to a
    short domain + a couple of meaningful keywords."""
    meaningful_keywords = [k for k in understanding.keywords if k.lower() not in GENERIC_KEYWORDS]
    terms = [understanding.domain, *meaningful_keywords[:MAX_KAGGLE_KEYWORDS]]

    deduped = []
    for term in terms:
        if term and term not in deduped:
            deduped.append(term)
    return " ".join(deduped)


def _candidate_datasets(understanding: QueryAnalysisResult, k: int) -> List[DatasetMatch]:
    """Curated catalog matches plus any live Kaggle matches (best-effort;
    empty when KAGGLE_API_TOKEN isn't configured)."""
    catalog_matches = search_datasets(_discovery_query(understanding), k=k).matches
    external_matches = [
        DatasetMatch(**item) for item in collect_external_datasets(_kaggle_query(understanding), limit=k)
    ]
    return catalog_matches + external_matches


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


@app.post("/dataset-collection-agent", response_model=List[DatasetMatch])
def dataset_collection_agent(query: str, k: int = DEFAULT_RESULT_COUNT):
    return [DatasetMatch(**item) for item in collect_external_datasets(query, limit=k)]


@app.post("/evaluation-agent", response_model=List[EvaluatedDataset])
def evaluation_agent(query: str, k: int = DEFAULT_RESULT_COUNT):
    try:
        understanding = analyze_query(query)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc

    candidates = _candidate_datasets(understanding, k)
    return evaluate_datasets(candidates, understanding)


@app.post("/discover", response_model=DiscoverResponse)
def discover(
    query: str,
    k: int = DEFAULT_RESULT_COUNT,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Full pipeline: NLP Agent -> Discovery Agent (+ live Kaggle results when
    configured) -> Evaluation Agent. Stays usable without an account; if a
    valid token IS attached, the search is additionally recorded against
    that user to power GET /recommendations. Anonymous searches are never
    recorded anywhere."""
    try:
        understanding = analyze_query(query)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc

    candidates = _candidate_datasets(understanding, k)
    recommendations = evaluate_datasets(candidates, understanding)

    if current_user is not None:
        record_search(db, current_user, understanding)

    return DiscoverResponse(understanding=understanding, recommendations=recommendations)


@app.get("/recommendations", response_model=RecommendationResponse)
def recommendations(
    k: int = DEFAULT_RESULT_COUNT,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Personalized recommendations based on the signed-in user's own search
    pattern (most frequent domain/task across their history) — not a fresh
    query. Empty history returns an empty list, not an error."""
    return get_recommendations(db, current_user, k=k)


@app.delete("/recommendations", status_code=204)
def delete_search_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lets a user clear their own search history — Responsible AI: personalization
    should be optional and reversible, not a silent permanent record."""
    clear_history(db, current_user)
