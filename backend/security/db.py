import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from .database_config import database_url

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "database" / "app.db"
DATABASE_URL = database_url(os.getenv("DATABASE_URL"), DEFAULT_DB_PATH, vercel=os.getenv("VERCEL") == "1")
sqlite = DATABASE_URL.get_backend_name() == "sqlite"
if sqlite and DATABASE_URL.database and DATABASE_URL.database != ":memory:":
    Path(DATABASE_URL.database).parent.mkdir(parents=True, exist_ok=True)
# The provider's pooled endpoint manages PostgreSQL connections. Avoid a
# separate pool retained by every serverless instance.
engine_options = {"connect_args": {"check_same_thread": False}} if sqlite else {}
if DATABASE_URL.get_backend_name() == "postgresql":
    engine_options.update(poolclass=NullPool, connect_args={"connect_timeout": 10, "prepare_threshold": None})
engine = create_engine(DATABASE_URL, pool_pre_ping=True, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from .encryption import _cipher
    _cipher()  # Fail before database changes if the persistent key is missing/invalid.
    with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            # Concurrent cold starts must not race schema creation/migration.
            connection.execute(text("SELECT pg_advisory_xact_lock(682409110)"))
        _init_schema(connection)


def _init_schema(connection):
    from .encryption import PREFIX, decrypt_stored_text, encrypt_stored_text
    Base.metadata.create_all(bind=connection)
    # Additive migration for existing local catalogs. Unknown modalities remain
    # unknown; only unchanged original seed entries can be identified as tabular.
    columns = {column["name"] for column in inspect(connection).get_columns("catalog_datasets")}
    if "data_type" not in columns:
        import json
        seeds = json.loads((Path(__file__).resolve().parents[1] / "agents/discovery_agent/datasets.json").read_text())
        connection.execute(text("ALTER TABLE catalog_datasets ADD COLUMN data_type VARCHAR"))
        for entry in seeds:
            connection.execute(text("UPDATE catalog_datasets SET data_type = 'tabular' WHERE name = :name AND description = :description AND domain = :domain AND task = :task"), {key: entry[key] for key in ("name", "description", "domain", "task")})

    # Minimize identifiers in legacy history without deleting quota/profile rows.
    from responsible_ai.privacy import redact_sensitive_text
    import hashlib
    for row in connection.execute(text("SELECT id, query FROM search_history")).all():
        plaintext = decrypt_stored_text(row.query)
        cleaned = redact_sensitive_text(plaintext)
        if not row.query.startswith(PREFIX) or cleaned != plaintext:
            connection.execute(text("UPDATE search_history SET query = :query WHERE id = :id"), {"id": row.id, "query": encrypt_stored_text(cleaned)})
    for row in connection.execute(text("SELECT id, token FROM password_reset_tokens")).all():
        if len(row.token) != 64:
            connection.execute(text("UPDATE password_reset_tokens SET token = :token, used = true WHERE id = :id"), {"id": row.id, "token": hashlib.sha256(row.token.encode()).hexdigest()})


def lock_seed(session, key: int) -> None:
    if session.get_bind().dialect.name == "postgresql":
        session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
