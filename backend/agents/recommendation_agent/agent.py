from collections import Counter
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from agents.discovery_agent.agent import search_datasets
from agents.evaluation_agent.agent import evaluate_datasets
from agents.nlp_agent.models import QueryAnalysisResult
from security.db_models import SearchHistory, User

from .models import RecommendationResponse

MAX_HISTORY_FOR_PROFILE = 50
DEFAULT_RECOMMENDATION_COUNT = 3


def record_search(db: Session, user: User, understanding: QueryAnalysisResult) -> None:
    """Only ever called for a signed-in user (see main.py's /discover) —
    anonymous searches are never written anywhere."""
    entry = SearchHistory(
        user_id=user.id,
        query=understanding.original_query,
        domain=understanding.domain,
        task=understanding.task,
    )
    db.add(entry)
    db.commit()


def _build_profile(db: Session, user: User) -> Tuple[Optional[str], Optional[str], int]:
    """Pattern analysis: the user's most frequent domain and task across
    their recent search history. Deliberately simple (mode, not a learned
    model) so it's easy to explain and to justify in the viva."""
    history = (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(MAX_HISTORY_FOR_PROFILE)
        .all()
    )
    if not history:
        return None, None, 0

    top_domain = Counter(entry.domain for entry in history).most_common(1)[0][0]
    top_task = Counter(entry.task for entry in history).most_common(1)[0][0]
    return top_domain, top_task, len(history)


def get_recommendations(db: Session, user: User, k: int = DEFAULT_RECOMMENDATION_COUNT) -> RecommendationResponse:
    top_domain, top_task, count = _build_profile(db, user)
    if top_domain is None:
        return RecommendationResponse(based_on_domain=None, based_on_task=None, search_count=0, recommendations=[])

    # Catalog only, no live Kaggle call: this runs speculatively (e.g. on
    # every homepage load for a signed-in user) rather than in response to a
    # specific query, so it deliberately avoids an external API round-trip
    # per page view. Live search still covers Kaggle as usual.
    profile_query = f"{top_domain} {top_task}"
    profile = QueryAnalysisResult(
        original_query=profile_query,
        domain=top_domain,
        task=top_task,
        data_type="tabular",
        keywords=[],
        understanding_source="rule_based",
    )
    matches = search_datasets(profile_query, k=k).matches
    recommendations = evaluate_datasets(matches, profile)

    return RecommendationResponse(
        based_on_domain=top_domain,
        based_on_task=top_task,
        search_count=count,
        recommendations=recommendations,
    )


def clear_history(db: Session, user: User) -> int:
    """Returns the number of rows deleted, so the caller can confirm to the user."""
    deleted = db.query(SearchHistory).filter(SearchHistory.user_id == user.id).delete()
    db.commit()
    return deleted
