import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "database" / "app.db"
DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
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
    from .encryption import _cipher, PREFIX, decrypt_stored_text, encrypt_stored_text
    _cipher()  # Fail before database changes if the persistent key is missing/invalid.
    Base.metadata.create_all(bind=engine)
    # Additive migration for existing local catalogs. Unknown modalities remain
    # unknown; only unchanged original seed entries can be identified as tabular.
    columns = {column["name"] for column in inspect(engine).get_columns("catalog_datasets")}
    if "data_type" not in columns:
        import json
        seeds = json.loads((Path(__file__).resolve().parents[1] / "agents/discovery_agent/datasets.json").read_text())
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE catalog_datasets ADD COLUMN data_type VARCHAR"))
            for entry in seeds:
                connection.execute(text("UPDATE catalog_datasets SET data_type = 'tabular' WHERE name = :name AND description = :description AND domain = :domain AND task = :task"), {key: entry[key] for key in ("name", "description", "domain", "task")})

    # Minimize identifiers in legacy history without deleting quota/profile rows.
    from responsible_ai.privacy import redact_sensitive_text
    import hashlib
    with engine.begin() as connection:
        for row in connection.execute(text("SELECT id, query FROM search_history")).all():
            plaintext = decrypt_stored_text(row.query)
            cleaned = redact_sensitive_text(plaintext)
            if not row.query.startswith(PREFIX) or cleaned != plaintext:
                connection.execute(text("UPDATE search_history SET query = :query WHERE id = :id"), {"id": row.id, "query": encrypt_stored_text(cleaned)})
        for row in connection.execute(text("SELECT id, token FROM password_reset_tokens")).all():
            if len(row.token) != 64:
                connection.execute(text("UPDATE password_reset_tokens SET token = :token, used = true WHERE id = :id"), {"id": row.id, "token": hashlib.sha256(row.token.encode()).hexdigest()})
