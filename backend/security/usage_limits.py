from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .db_models import AnonymousSearchLog, Plan, SearchHistory, User

FREE_PLAN_NAME = "free"


def get_plan_by_name(db: Session, name: str) -> Optional[Plan]:
    return db.query(Plan).filter(Plan.name == name).first()


def _start_of_today() -> datetime:
    """UTC midnight, not the caller's local midnight — a known
    simplification, not per-user-timezone-aware. A user near the
    international date line could see their count reset at an odd local
    hour; acceptable for this project's scope, not claimed as more precise
    than it is."""
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _count_since(db: Session, model, filter_column, filter_value) -> int:
    since = _start_of_today()
    return (
        db.query(func.count(model.id))
        .filter(filter_column == filter_value, model.created_at >= since)
        .scalar()
        or 0
    )


def get_usage(db: Session, user: Optional[User], ip_address: str) -> tuple[str, Optional[int], int]:
    """Returns (plan_name, limit, used_today). limit of None = unlimited."""
    if user is not None:
        used = _count_since(db, SearchHistory, SearchHistory.user_id, user.id)
        # Admins bypass the plan's limit entirely, regardless of which plan
        # they're actually on — being an admin should mean unlimited access,
        # not "unlimited if someone also remembered to put them on a
        # no-limit plan." `used` is still the real count, just never
        # compared against a limit (see enforce_search_limit below).
        if user.is_admin:
            return user.plan, None, used
        plan = get_plan_by_name(db, user.plan)
        limit = plan.daily_search_limit if plan else None
        return user.plan, limit, used

    plan = get_plan_by_name(db, FREE_PLAN_NAME)
    limit = plan.daily_search_limit if plan else None
    used = _count_since(db, AnonymousSearchLog, AnonymousSearchLog.ip_address, ip_address)
    return FREE_PLAN_NAME, limit, used


def enforce_search_limit(db: Session, user: Optional[User], ip_address: str) -> None:
    """Raises 429 if the caller has hit their plan's daily search limit.
    Signed-in users are checked against their own plan (falling back to the
    Free limit if their plan was deleted from under them); anonymous
    callers are always checked against the Free plan's limit, tracked by
    IP so logging out can't be used to bypass it.

    Deliberately called BEFORE running the actual NLP/Discovery/Evaluation
    pipeline in main.py, so a request that's about to be rejected doesn't
    still burn a real Gemini/Kaggle/OpenML/HuggingFace call first.
    """
    plan_name, limit, used = get_usage(db, user, ip_address)
    if limit is None:
        return

    if used >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Daily search limit reached ({limit}/day on the {plan_name} plan). "
                "Try again tomorrow, or upgrade to Pro for unlimited searches."
            ),
        )


def record_anonymous_search(db: Session, ip_address: str) -> None:
    db.add(AnonymousSearchLog(ip_address=ip_address))
    db.commit()
