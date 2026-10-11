"""Run Subasthican's 30 recorded prompt-security cases in an isolated database."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
started = datetime.now(ZoneInfo("Asia/Colombo"))
output = ROOT / "docs/viva/test-runs" / started.strftime("%Y%m%d-%H%M%S-%f")
output.mkdir(parents=True)
database = ROOT / "database/app.db"
before = hashlib.sha256(database.read_bytes()).hexdigest() if database.exists() else None
baseline = json.loads((ROOT / "docs/individual-assessments/evidence/results.json").read_text())
cases = [case for case in baseline if case["test_id"].startswith("PI-")]
assert len(cases) == 30, "Expected the 15 PI and 15 PI-V recorded scenarios."
results = []

with tempfile.TemporaryDirectory(prefix="nebula-prompt-viva-") as temporary:
    os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(temporary) / "test.db")
    os.environ["JWT_SECRET_KEY"] = secrets.token_hex(32)
    from cryptography.fernet import Fernet
    os.environ["DATA_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
    sys.path.insert(0, str(ROOT / "backend"))
    from fastapi.testclient import TestClient
    import main
    from agents.nlp_agent import agent as nlp
    from security.db import SessionLocal, engine
    from security.db_models import User

    print("LIVE EXECUTION: application guards and controlled output fixtures", flush=True)
    print("No live Gemini calls. Temporary synthetic database.\n", flush=True)
    try:
        with TestClient(main.app, raise_server_exceptions=False) as client:
            response = client.post("/auth/register", json={
                "name": "Prompt viva fixture", "email": "prompt-viva@example.com",
                "password": "SyntheticOnly-" + secrets.token_hex(12),
            })
            assert response.status_code == 201, "Synthetic account setup failed."
            headers = {"Authorization": "Bearer " + response.json()["access_token"]}
            user_id = client.get("/auth/me", headers=headers).json()["id"]
            with SessionLocal() as db:
                db.get(User, user_id).is_admin = True
                db.commit()

            for case in cases:
                ident = case["test_id"]
                try:
                    if ident.startswith("PI-V"):
                        scenario = case["input_scenario"]
                        raw = scenario["controlled_model_response"]
                        with patch.object(nlp, "generate_response", return_value=raw):
                            analysis = nlp.analyze_query(scenario["user_query"])
                        rejected = nlp._parse_llm_json(raw) is None
                        actual = {"source": analysis.understanding_source, "parsed_rejected": rejected}
                        passed = rejected and analysis.understanding_source == "rule_based"
                        expected = "Reject malformed fixture and use rule-based fallback."
                    else:
                        with patch.object(nlp, "generate_response") as provider:
                            response = client.post("/nlp-agent", params={"query": case["input_scenario"]}, headers=headers)
                        actual = {"status": response.status_code, "provider_called": provider.called, "response": response.json()}
                        passed = response.status_code == 400 and not provider.called
                        expected = "HTTP 400 before provider invocation."
                    outcome = "PASS" if passed else "FAIL"
                except Exception as error:
                    outcome = "ERROR"
                    actual = {"error_type": type(error).__name__, "message": str(error)}
                    expected = "Safe handling of the recorded scenario."
                record = {"test_id": ident, "objective": case["objective"],
                          "input_scenario": case["input_scenario"], "expected": expected,
                          "actual": actual, "outcome": outcome,
                          "scope": "Application guard or controlled fixture; no live provider resistance measured."}
                results.append(record)
                (output / f"{ident}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
                print(f"{ident}: {outcome} | {case['objective']}", flush=True)
                if ident in {"PI-01", "PI-V10"}:
                    print("  Actual: " + json.dumps(actual, ensure_ascii=False), flush=True)
    finally:
        engine.dispose()

after = hashlib.sha256(database.read_bytes()).hexdigest() if database.exists() else None
counts = {status: sum(case["outcome"] == status for case in results) for status in ("PASS", "FAIL", "ERROR")}
manifest = {"executed_at": started.isoformat(), "counts": counts,
            "original_database_unchanged": before == after,
            "scope": "15 input guards and 15 controlled outputs; no live Gemini evaluation.",
            "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in (ROOT / "backend").rglob("*")
                              if path.is_file() and path.suffix in {".py", ".json"} and "__pycache__" not in path.parts}}
(output / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
(output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("\nYour 30 cases: " + json.dumps(counts), flush=True)
print("Original database unchanged: " + str(before == after), flush=True)
print("Fresh evidence: " + str(output), flush=True)
if len(results) != 30 or counts["FAIL"] or counts["ERROR"] or before != after:
    sys.exit(1)
