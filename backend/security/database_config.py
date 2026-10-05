"""Database configuration without opening a connection or printing credentials."""
from pathlib import Path

from sqlalchemy.engine import make_url


def database_url(value: str | None, default_path: Path, *, vercel: bool = False):
    if vercel and not value:
        raise ValueError("Set DATABASE_URL to a hosted PostgreSQL connection for Vercel.")
    raw = value or f"sqlite:///{default_path}"
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://"):]
    try:
        url = make_url(raw)
    except Exception:
        raise ValueError("DATABASE_URL must be a valid SQLAlchemy connection URL.") from None
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    if vercel and url.get_backend_name() != "postgresql":
        raise ValueError("Vercel requires a hosted PostgreSQL database; local SQLite is not persistent.")
    return url
