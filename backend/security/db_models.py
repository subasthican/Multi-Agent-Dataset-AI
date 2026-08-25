import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    plan: Mapped[str] = mapped_column(String, default="free", nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Reversible alternative to deleting an account outright — a suspended
    # user can't log in, and an already-issued token stops working
    # immediately (re-checked on every request, same as is_admin; see
    # authentication.py). Re-activating just flips this back.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    search_history: Mapped[list["SearchHistory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="reset_tokens")


class SearchHistory(Base):
    """One row per search a *signed-in* user makes. Anonymous searches are
    never recorded anywhere — this table only exists to power personalized
    recommendations for logged-in users, and only for them (see
    security/router.py's transparency note and the DELETE /recommendations
    endpoint that lets a user clear it)."""

    __tablename__ = "search_history"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True, nullable=False)
    query: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    task: Mapped[str] = mapped_column(String, nullable=False)
    understanding_source: Mapped[str] = mapped_column(String, default="rule_based", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["User"] = relationship(back_populates="search_history")


class CatalogDataset(Base):
    """The Discovery Agent's curated local catalog — used to live as a
    static datasets.json file (still there, now used only to seed this
    table on first startup so the original 10 entries aren't lost). Lives
    here alongside the other DB models rather than in discovery_agent/
    because that's where Base/the shared session already live, not because
    it's a security concern."""

    __tablename__ = "catalog_datasets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    task: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class Plan(Base):
    """A pricing tier. `name` is the stable key User.plan stores (e.g.
    "free", "pro") — deliberately not a foreign key, so a plan can be
    edited/deleted-checked without touching User rows directly; see
    admin_router.py for how a delete is blocked while any user still holds
    that name. `daily_search_limit` of None means unlimited."""

    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    price_label: Mapped[str] = mapped_column(String, nullable=False)
    period: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    features: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    daily_search_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class AnonymousSearchLog(Base):
    """One row per search made *without* being signed in, tracked by IP so
    the Free plan's daily limit applies to anonymous use too (otherwise
    logging out would trivially bypass it). Deliberately separate from
    SearchHistory, which is keyed to a user_id and powers recommendations -
    this table exists purely for rate limiting, nothing reads it back for
    any personalization purpose.

    Known limitation: request.client.host is the direct TCP peer, not the
    real client IP behind a reverse proxy (no X-Forwarded-For handling) -
    fine for local/direct deployment, would need revisiting behind a proxy.
    """

    __tablename__ = "anonymous_search_log"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    ip_address: Mapped[str] = mapped_column(String, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
