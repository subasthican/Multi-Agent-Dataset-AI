"""Atomic daily reservations shared by all public AI routes."""
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db_models import AnonymousSearchLog, Plan, SearchHistory, SearchUsage, User
from .jwt_manager import SECRET_KEY

FREE_PLAN_NAME = "free"
DEFAULT_FREE_LIMIT = 10


def get_plan_by_name(db, name):
    return db.query(Plan).filter(Plan.name == name).first()


def _start_of_today():
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _subject(user, ip):
    if user is not None:
        return "user:" + user.id
    return "peer:" + hmac.new(SECRET_KEY.encode(), ip.encode(), hashlib.sha256).hexdigest()


def _legacy_usage(db, user, ip):
    model = SearchHistory if user else AnonymousSearchLog
    column = SearchHistory.user_id if user else AnonymousSearchLog.ip_address
    value = user.id if user else ip
    return db.query(func.count(model.id)).filter(column == value, model.created_at >= _start_of_today()).scalar() or 0


def get_usage(db: Session, user: Optional[User], ip_address: str):
    row = db.get(SearchUsage, (_subject(user, ip_address), _start_of_today().date().isoformat()))
    used = row.count if row else _legacy_usage(db, user, ip_address)
    name = user.plan if user else FREE_PLAN_NAME
    if user and user.is_admin:
        return name, None, used
    plan = get_plan_by_name(db, name) or get_plan_by_name(db, FREE_PLAN_NAME)
    return name, plan.daily_search_limit if plan else DEFAULT_FREE_LIMIT, used


def enforce_search_limit(db: Session, user: Optional[User], ip_address: str):
    """Reserve a request before provider work; even concurrent requests count.

    Accepted requests consume a slot even if downstream services fail. This avoids
    using provider failures or history deletion to erase resource usage.
    """
    name, limit, legacy = get_usage(db, user, ip_address)
    subject, day = _subject(user, ip_address), _start_of_today().date().isoformat()
    if db.get(SearchUsage, (subject, day)) is None:
        try:
            with db.begin_nested():
                db.add(SearchUsage(subject=subject, day=day, count=legacy))
                db.flush()
        except IntegrityError:
            # Another request initialized this same counter.
            pass
    statement = update(SearchUsage).where(SearchUsage.subject == subject, SearchUsage.day == day)
    if limit is not None:
        statement = statement.where(SearchUsage.count < limit)
    changed = db.execute(statement.values(count=SearchUsage.count + 1)).rowcount
    db.commit()
    if not changed:
        raise HTTPException(status_code=429, detail=f"Daily search limit reached ({limit}/day on the {name} plan).")


def record_anonymous_search(db, ip_address):
    # Reservation above already records usage without retaining plaintext IPs.
    pass
