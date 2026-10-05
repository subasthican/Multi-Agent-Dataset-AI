"""Disposable local fixture for manual duplicate/fallback browser verification.

No production database or live provider calls. Terminal-created synthetic login:
browser-user@example.com / BrowserTest123! (not a real credential).
"""
import os
from pathlib import Path
import secrets
import sys
import tempfile

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix="nebula-duplicate-browser-") as directory:
    os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(directory) / "browser.db")
    os.environ["DATA_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
    os.environ["JWT_SECRET_KEY"] = secrets.token_hex(32)
    os.environ["ALLOWED_ORIGINS"] = "http://localhost:3015,http://127.0.0.1:3015"
    os.environ["SMTP_HOST"] = ""
    os.environ["SMTP_FROM"] = ""
    sys.path.insert(0, str(ROOT / "backend"))
    import main
    import uvicorn
    from fastapi.testclient import TestClient
    from agents.nlp_agent import agent as nlp
    from llm.gemini_client import LLMUnavailableError
    from security.db import SessionLocal
    from security.db_models import CatalogDataset

    def offline_provider(prompt):
        raise LLMUnavailableError("Declared browser fallback fixture; no remote request")

    nlp.generate_response = offline_provider
    fields = {"name": "Diabetes duplicate verification", "description": "Medical patient records with glucose, BMI and age for diabetes classification",
              "domain": "healthcare", "task": "classification", "data_type": "tabular"}
    with TestClient(main.app) as client:
        result = client.post("/auth/register", json={"name": "Browser Fixture User", "email": "browser-user@example.com", "password": "BrowserTest123!"})
        assert result.status_code == 201
    with SessionLocal() as db:
        db.add(CatalogDataset(**fields, url="https://www.kaggle.com/datasets/example/diabetes-fixture"))
        db.commit()

    def fixture_sources(query, limit=5):
        return [{**fields, "id": "example/diabetes-fixture", "source": "kaggle", "similarity": 0.95,
                 "url": "http://kaggle.com/datasets/example/diabetes-fixture/?utm_source=fixture#files"},
                {**fields, "name": "Independent diabetes source", "id": "example/independent", "source": "huggingface", "similarity": 0.90,
                 "url": "https://huggingface.co/datasets/example/independent"}][:limit]

    main.collect_external_datasets = fixture_sources
    uvicorn.run(main.app, host="127.0.0.1", port=8015)
