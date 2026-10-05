"""Local disposable PostgreSQL validation; requires PostgreSQL binaries.

No cloud account/database connection or real provider calls. No real app data.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[2]
binary = {name: shutil.which(name) for name in ("initdb", "pg_ctl")}
if not all(binary.values()):
    sys.exit("Install PostgreSQL locally so initdb and pg_ctl are available.")
before = hashlib.sha256((ROOT / "database/app.db").read_bytes()).hexdigest()
cases = []


def check(name, ok, details=None):
    cases.append({"check": name, "outcome": "PASS" if ok else "FAIL", "details": details})
    assert ok, name


with tempfile.TemporaryDirectory(prefix="nebula-postgres-") as directory:
    scratch = Path(directory)
    data = scratch / "pgdata"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    subprocess.run([binary["initdb"], "-D", str(data), "--auth=trust", "--username=nebula_test", "--no-locale", "-E", "UTF8"], check=True, capture_output=True)
    subprocess.run([binary["pg_ctl"], "-D", str(data), "-l", str(scratch / "postgres.log"), "-o", f"-h 127.0.0.1 -p {port} -k {scratch}", "-w", "start"], check=True, capture_output=True)
    try:
        os.environ["DATABASE_URL"] = f"postgresql://nebula_test@127.0.0.1:{port}/postgres"
        os.environ["DATA_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
        os.environ["JWT_SECRET_KEY"] = secrets.token_hex(32)
        os.environ["SMTP_HOST"] = ""
        os.environ["SMTP_FROM"] = ""
        os.environ["VERCEL"] = "1"
        sys.path.insert(0, str(ROOT / "backend"))
        import main
        from fastapi.testclient import TestClient
        from sqlalchemy import text
        from security.db import SessionLocal, engine
        from security.db_models import User, CatalogDataset
        from agents.discovery_agent.agent import search_datasets
        from security.password_reset import create_reset_token
        from llm.gemini_client import LLMUnavailableError
        from agents.nlp_agent import agent as nlp

        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(lambda _: main.on_startup(), range(4)))
        with engine.connect() as connection:
            catalog = connection.execute(text("SELECT COUNT(*) FROM catalog_datasets")).scalar_one()
            plans = connection.execute(text("SELECT COUNT(*) FROM plans")).scalar_one()
        check("Concurrent cloud startup and seed uniqueness", catalog == 10 and plans == 3, {"catalog": catalog, "plans": plans})

        with patch.object(nlp, "generate_response", side_effect=LLMUnavailableError("Declared PostgreSQL fallback fixture")), patch.object(main, "collect_external_datasets", return_value=[]), TestClient(main.app) as client:
            password = "PostgresFixture123!"
            result = client.post("/auth/register", json={"name": "Synthetic PostgreSQL User", "email": "postgres-user@example.com", "password": password})
            check("Registration", result.status_code == 201)
            headers = {"Authorization": "Bearer " + result.json()["access_token"]}
            check("Persistent JWT authentication", client.get("/auth/me", headers=headers).status_code == 200)
            result = client.post("/discover", params={"query": "Find healthcare datasets for diabetes classification"}, headers=headers)
            check("Bundled offline model and full search pipeline", result.status_code == 200 and result.json()["recommendations"][0]["dataset"]["name"] == "Diabetes Prediction Dataset")
            with engine.connect() as connection:
                raw = connection.execute(text("SELECT query FROM search_history")).scalar_one()
            check("Stored query encryption", raw.startswith("fernet:v1:") and "diabetes" not in raw)
            result = client.get("/recommendations", headers=headers)
            check("Authorized recommendation readback", result.status_code == 200 and result.json()["search_count"] == 1)
            main.on_startup()
            with engine.connect() as connection:
                after = connection.execute(text("SELECT query FROM search_history")).scalar_one()
            check("Repeat migration retains ciphertext", after == raw)
            check("Ordinary user admin denial", client.get("/admin/audit", headers=headers).status_code == 403)

            with SessionLocal() as db:
                user = db.query(User).filter(User.email == "postgres-user@example.com").one()
                user.is_admin = True
                db.commit()
            payload = {"name": "PostgreSQL fixture", "description": "Medical diabetes classification table", "domain": "healthcare", "task": "classification", "data_type": "tabular", "url": "https://example.com/data"}
            result = client.post("/admin/catalog", headers=headers, json=payload)
            check("Catalog creation and JSON audit fields", result.status_code == 201)
            ident = result.json()["id"]
            search_datasets("medical diabetes", k=20)
            with SessionLocal() as db:
                db.get(CatalogDataset, ident).name = "Changed in another cloud worker"
                db.commit()  # No in-process cache invalidation: simulate another instance.
            matches = search_datasets("medical diabetes", k=20).matches
            check("Shared catalog freshness across cloud workers", any(match.id == ident and match.name == "Changed in another cloud worker" for match in matches))
            check("Catalog update", client.patch(f"/admin/catalog/{ident}", headers=headers, json={"description": "Updated medical diabetes table"}).status_code == 200)
            check("Password confirmation denial", client.request("DELETE", f"/admin/catalog/{ident}", headers=headers, json={"password": "WrongPassword123!"}).status_code == 403)
            check("Password-confirmed deletion", client.request("DELETE", f"/admin/catalog/{ident}", headers=headers, json={"password": password}).status_code == 204)
            events = client.get("/admin/audit", headers=headers).json()
            check("Audit survives deletion", any(event["target_id"] == ident and event["action"] == "delete" for event in events))

            check("Password update", client.post("/auth/change-password", headers=headers, json={"current_password": password, "new_password": "PostgresChanged123!"}).status_code == 204)
            check("Old JWT revoked", client.get("/auth/me", headers=headers).status_code == 401)
            with SessionLocal() as db:
                user = db.query(User).filter(User.email == "postgres-user@example.com").one()
                token = create_reset_token(db, user)
            check("Password recovery capability", client.post("/auth/reset-password", json={"token": token, "new_password": "PostgresReset123!"}).status_code == 204)
            check("Recovery capability single use", client.post("/auth/reset-password", json={"token": token, "new_password": "PostgresAnother123!"}).status_code == 400)

            result = client.post("/auth/register", json={"name": "Synthetic Quota User", "email": "postgres-quota@example.com", "password": password})
            quota_headers = {"Authorization": "Bearer " + result.json()["access_token"]}
            with ThreadPoolExecutor(max_workers=6) as executor:
                statuses = list(executor.map(lambda _: client.post("/nlp-agent", params={"query": "Find diabetes prediction datasets"}, headers=quota_headers).status_code, range(12)))
            check("Concurrent daily reservation", statuses.count(200) == 10 and statuses.count(429) == 2, {"accepted": statuses.count(200), "limited": statuses.count(429)})
            client.delete("/recommendations", headers=quota_headers)
            check("History deletion preserves quota", client.get("/usage", headers=quota_headers).json()["remaining"] == 0)
            peer_a = {"X-Forwarded-For": "203.0.113.10"}
            peer_b = {"X-Forwarded-For": "203.0.113.11"}
            client.post("/nlp-agent", params={"query": "Find diabetes prediction datasets"}, headers=peer_a)
            a = client.get("/usage", headers=peer_a).json()["used"]
            b = client.get("/usage", headers=peer_b).json()["used"]
            check("Independent anonymous platform-IP quotas", a == 1 and b == 0, {"peer_a_used": a, "peer_b_used": b})
    finally:
        subprocess.run([binary["pg_ctl"], "-D", str(data), "-m", "fast", "-w", "stop"], check=True, capture_output=True)

unchanged = before == hashlib.sha256((ROOT / "database/app.db").read_bytes()).hexdigest()
check("Working SQLite database unchanged", unchanged)
report = {"checked_at": datetime.now(ZoneInfo("Asia/Colombo")).isoformat(), "scope": "Real isolated PostgreSQL 15, Vercel-mode configuration and bundled model; remote Gemini/external retrieval explicitly unavailable/mocked. Not a Neon or deployed Vercel test.",
          "counts": {state: sum(case["outcome"] == state for case in cases) for state in ("PASS", "FAIL")}, "cases": cases}
(ROOT / "docs/fix-verification/evidence/postgres-validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report), flush=True)
