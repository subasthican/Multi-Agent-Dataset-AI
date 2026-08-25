import os
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from agents.dataset_collection_agent.agent import collect_external_datasets
from agents.discovery_agent.agent import search_datasets
from agents.discovery_agent.models import DatasetMatch, DiscoveryResult
from agents.discovery_agent.seed import seed_catalog_if_empty
from agents.evaluation_agent.agent import evaluate_datasets
from agents.evaluation_agent.models import EvaluatedDataset
from agents.nlp_agent.agent import analyze_query
from agents.nlp_agent.models import QueryAnalysisResult
from agents.recommendation_agent.agent import clear_history, get_recommendations, record_search
from agents.recommendation_agent.models import RecommendationResponse
from security.admin_router import router as admin_router
from security.authentication import get_current_user, get_current_user_optional
from security.db import get_db, init_db
from security.db_models import Plan, User
from security.plan_seed import seed_plans_if_empty
from security.router import router as auth_router
from security.schemas import PlanResponse, UsageResponse
from security.usage_limits import enforce_search_limit, get_usage, record_anonymous_search

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
app.include_router(admin_router)


@app.on_event("startup")
def on_startup():
    init_db()
    seed_catalog_if_empty()
    seed_plans_if_empty()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"

DEFAULT_RESULT_COUNT = 3
# Unbounded k previously passed straight through to Kaggle/OpenML/HuggingFace's
# own `limit` params with no validation — found while auditing the Discovery
# Agent. Those APIs likely cap it themselves, but nothing on our side did.
MAX_RESULT_COUNT = 20
ResultCount = Query(default=DEFAULT_RESULT_COUNT, ge=1, le=MAX_RESULT_COUNT)

# Terms too generic to help any external source's own search (Kaggle,
# OpenML, HuggingFace all confirmed to return nothing for long, noisy
# multi-keyword strings — they need a short, specific query).
GENERIC_KEYWORDS = {"dataset", "datasets", "data", "machine", "learning", "predicting", "prediction"}
MAX_EXTERNAL_KEYWORDS = 2


class DiscoverResponse(BaseModel):
    understanding: QueryAnalysisResult
    recommendations: List[EvaluatedDataset]


def _discovery_query(understanding: QueryAnalysisResult) -> str:
    """Query for the FAISS-embedded catalog search — embeddings handle a
    longer, denser bag of terms fine."""
    return " ".join([understanding.domain, understanding.task, *understanding.keywords])


def _external_query(understanding: QueryAnalysisResult) -> str:
    """Query for Kaggle/OpenML/HuggingFace's own search endpoints, which —
    unlike FAISS similarity — return zero results for long multi-keyword
    strings, so this stays to a short domain + a couple of meaningful
    keywords. (OpenML narrows this further itself, to just the first word.)"""
    meaningful_keywords = [k for k in understanding.keywords if k.lower() not in GENERIC_KEYWORDS]
    terms = [understanding.domain, *meaningful_keywords[:MAX_EXTERNAL_KEYWORDS]]

    deduped = []
    for term in terms:
        if term and term not in deduped:
            deduped.append(term)
    return " ".join(deduped)


def _candidate_datasets(understanding: QueryAnalysisResult, k: int) -> List[DatasetMatch]:
    """Curated catalog matches plus any live external matches from Kaggle,
    OpenML, and HuggingFace (each best-effort — an unconfigured or
    unreachable source just contributes nothing, never an error)."""
    catalog_matches = search_datasets(_discovery_query(understanding), k=k).matches
    external_matches = [
        DatasetMatch(**item) for item in collect_external_datasets(_external_query(understanding), limit=k)
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
def discovery_agent(query: str, k: int = ResultCount):
    return search_datasets(query, k=k)


@app.post("/dataset-collection-agent", response_model=List[DatasetMatch])
def dataset_collection_agent(query: str, k: int = ResultCount):
    return [DatasetMatch(**item) for item in collect_external_datasets(query, limit=k)]


@app.post("/evaluation-agent", response_model=List[EvaluatedDataset])
def evaluation_agent(query: str, k: int = ResultCount):
    try:
        understanding = analyze_query(query)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc

    candidates = _candidate_datasets(understanding, k)
    return evaluate_datasets(candidates, understanding)


@app.post("/discover", response_model=DiscoverResponse)
def discover(
    query: str,
    request: Request,
    k: int = ResultCount,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Full pipeline: NLP Agent -> Discovery Agent (+ live Kaggle results when
    configured) -> Evaluation Agent. Stays usable without an account.

    Every plan has a daily search limit (None = unlimited) — enforced
    BEFORE the pipeline runs, so a request that's about to be rejected
    doesn't still burn a real Gemini/Kaggle/OpenML/HuggingFace call. Signed-
    in users are checked against their own plan; anonymous callers are
    checked against the Free plan's limit, tracked by IP address (not the
    query text — see security/db_models.py's AnonymousSearchLog docstring)
    so logging out can't be used to bypass it.

    If a valid token IS attached, the search is additionally recorded
    against that user (query text + domain/task) to power
    GET /recommendations. Anonymous searches never have their query text
    stored anywhere — only an IP+timestamp counter for the limit above.
    """
    ip_address = _client_ip(request)
    enforce_search_limit(db, current_user, ip_address)

    try:
        understanding = analyze_query(query)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc

    candidates = _candidate_datasets(understanding, k)
    recommendations = evaluate_datasets(candidates, understanding)

    if current_user is not None:
        record_search(db, current_user, understanding)
    else:
        record_anonymous_search(db, ip_address)

    return DiscoverResponse(understanding=understanding, recommendations=recommendations)


@app.get("/plans", response_model=List[PlanResponse])
def list_plans(db: Session = Depends(get_db)):
    """Public — the pricing page needs this without requiring login."""
    return db.query(Plan).order_by(Plan.created_at).all()


@app.get("/usage", response_model=UsageResponse)
def usage(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Lets the frontend show "X of N searches used today" instead of only
    finding out via a 429 on the next search. Public — anonymous callers
    get their own IP-tracked usage."""
    plan_name, limit, used = get_usage(db, current_user, _client_ip(request))
    remaining = None if limit is None else max(0, limit - used)
    return UsageResponse(plan=plan_name, limit=limit, used=used, remaining=remaining)


@app.get("/recommendations", response_model=RecommendationResponse)
def recommendations(
    k: int = ResultCount,
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
