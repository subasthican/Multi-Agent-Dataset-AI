"""Run PR-01–PR-15 against real routes with synthetic data and mocked email.

From the repository root:
    venv/bin/python docs/individual-assessments/test_gowsika_privacy.py
Each execution saves a new evidence folder. No browser/server is required.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]


def main():
    started = datetime.now(ZoneInfo("Asia/Colombo"))
    output = ROOT / "docs/individual-assessments/privacy-test-runs" / started.strftime("%Y%m%d-%H%M%S-%f")
    output.mkdir(parents=True)
    working_db = ROOT / "database/app.db"

    def digest():
        return hashlib.sha256(working_db.read_bytes()).hexdigest() if working_db.exists() else None

    before = digest()
    results, secret_values = [], []

    def redacted(value):
        if isinstance(value, dict):
            return {key: "[REDACTED]" if key.lower() in {
                "access_token", "token", "password", "hashed_password", "current_password", "new_password"
            } else redacted(item) for key, item in value.items()}
        if isinstance(value, list):
            return [redacted(item) for item in value]
        if isinstance(value, str):
            for secret in secret_values:
                value = value.replace(secret, "[REDACTED]")
        return value

    def run(ident, objective, expected, function):
        try:
            passed, actual = function()
            outcome = "PASS" if passed else "FAIL"
        except Exception as error:
            outcome = "ERROR"
            actual = {"error_type": type(error).__name__, "message": str(error)}
        record = redacted({"test_id": ident, "objective": objective, "expected": expected,
                           "actual": actual, "outcome": outcome,
                           "scope": "Real in-process routes/components, temporary synthetic SQLite. Email and catalogue retrieval mocked; no SMTP or live provider calls."})
        results.append(record)
        (output / f"{ident}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        print(f"\n{ident}: {outcome} — {objective}", flush=True)
        print("  Expected: " + expected, flush=True)
        print("  Actual: " + json.dumps(record["actual"], ensure_ascii=False), flush=True)

    def summary(response):
        try:
            body = response.json()
        except ValueError:
            body = response.text
        return {"status": response.status_code, "body": body}

    with tempfile.TemporaryDirectory(prefix="nebula-privacy-viva-") as temporary:
        temp_db = Path(temporary) / "test.db"
        # Set isolation before importing anything that constructs the application engine.
        os.environ["DATABASE_URL"] = "sqlite:///" + str(temp_db)
        os.environ["JWT_SECRET_KEY"] = secrets.token_hex(32)
        from cryptography.fernet import Fernet
        os.environ["DATA_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
        os.environ["GEMINI_API_KEY"] = ""
        sys.path.insert(0, str(ROOT / "backend"))
        import jwt
        from sqlalchemy import text
        from fastapi.testclient import TestClient
        import main as application
        from security.db import SessionLocal, engine
        from security.db_models import User, SearchHistory, PasswordResetToken
        from security.authentication import verify_password
        from security.jwt_manager import SECRET_KEY, ALGORITHM
        from security.password_reset import create_reset_token
        from security.encryption import PREFIX
        from agents.nlp_agent.models import QueryAnalysisResult
        from agents.discovery_agent.models import DiscoveryResult
        from agents.recommendation_agent.agent import record_search
        from llm.prompts import dataset_prompt
        assert engine.url.get_backend_name() == "sqlite" and Path(engine.url.database).resolve() == temp_db.resolve(), "Database isolation failed."
        print("Gowsika privacy tests: real route execution, synthetic accounts, temporary database.", flush=True)
        print("Email delivery and recommendation retrieval use disclosed mocks.\n", flush=True)
        try:
            with patch("security.router.send_reset_email", return_value=True) as delivery, \
                 patch("agents.nlp_agent.agent.generate_response", side_effect=AssertionError("Unexpected provider call")), \
                 TestClient(application.app, raise_server_exceptions=False) as client:
                def account(name, admin=False):
                    password = "SyntheticOnly-" + secrets.token_hex(12)
                    secret_values.append(password)
                    email = f"privacy-{name}@example.com"
                    response = client.post("/auth/register", json={"name": "Synthetic " + name, "email": email, "password": password})
                    assert response.status_code == 201, "Synthetic registration failed."
                    token = response.json()["access_token"]
                    secret_values.append(token)
                    headers = {"Authorization": "Bearer " + token}
                    uid = client.get("/auth/me", headers=headers).json()["id"]
                    if admin:
                        with SessionLocal() as db:
                            db.get(User, uid).is_admin = True
                            db.commit()
                    return {"id": uid, "email": email, "password": password, "token": token, "headers": headers}

                def profile(token=None):
                    return client.get("/auth/me", headers={"Authorization": "Bearer " + token} if token else {})

                def history(user, domain, query="Synthetic dataset request"):
                    with SessionLocal() as db:
                        record_search(db, db.get(User, user["id"]), QueryAnalysisResult(
                            original_query=query, domain=domain, task="classification", data_type="tabular", keywords=[]))

                a, b, admin = account("a"), account("b"), account("admin", admin=True)
                run("PR-01", "Missing authentication", "HTTP 401 without account data.",
                    lambda: (lambda r: (r.status_code == 401, summary(r)))(profile()))
                tampered = a["token"].rsplit(".", 1)[0] + ".invalidsignature"
                run("PR-02", "Tampered JWT", "HTTP 401 for a modified signature.",
                    lambda: (lambda r: (r.status_code == 401, summary(r)))(profile(tampered)))
                expired = jwt.encode({"sub": a["id"], "exp": datetime.now(timezone.utc) - timedelta(seconds=1)}, SECRET_KEY, algorithm=ALGORITHM)
                secret_values.append(expired)
                run("PR-03", "Expired JWT", "HTTP 401 for an expired credential.",
                    lambda: (lambda r: (r.status_code == 401, summary(r)))(profile(expired)))

                def isolation():
                    history(a, "healthcare")
                    history(b, "finance")
                    other = client.get("/admin/users/" + b["id"], headers=a["headers"])
                    with patch("agents.recommendation_agent.agent.search_datasets", return_value=DiscoveryResult(query="fixture", matches=[])):
                        own_a = client.get("/recommendations", headers=a["headers"])
                        own_b = client.get("/recommendations", headers=b["headers"])
                    actual = {"other_account_status": other.status_code, "A_status": own_a.status_code,
                              "B_status": own_b.status_code, "A_domain": own_a.json().get("based_on_domain"),
                              "B_domain": own_b.json().get("based_on_domain")}
                    return other.status_code == 403 and own_a.status_code == own_b.status_code == 200 and actual["A_domain"] == "healthcare" and actual["B_domain"] == "finance", actual
                run("PR-04", "Cross-user isolation", "Other-account access denied; each profile uses its own history.", isolation)

                def authorization():
                    normal = [client.get(path, headers=a["headers"]) for path in ("/admin/users", "/admin/stats")]
                    permitted = client.get("/admin/users", headers=admin["headers"])
                    return all(r.status_code == 403 for r in normal) and permitted.status_code == 200, {"normal_user_statuses": [r.status_code for r in normal], "admin_status": permitted.status_code}
                run("PR-05", "Administrator authorization", "Normal users get 403; administrator gets 200.", authorization)

                def password_protection():
                    responses = [client.get("/auth/me", headers=a["headers"]), client.get("/admin/users", headers=admin["headers"])]
                    with SessionLocal() as db:
                        stored = db.get(User, a["id"]).hashed_password
                    bodies = "".join(r.text for r in responses)
                    hidden = stored not in bodies and a["password"] not in bodies and "hashed_password" not in bodies
                    hashed = stored != a["password"] and verify_password(a["password"], stored)
                    return all(r.status_code == 200 for r in responses) and hidden and hashed, {"statuses": [r.status_code for r in responses], "password_hash_verified": hashed, "credentials_absent_from_responses": hidden}
                run("PR-06", "Password protection", "Password is hashed and credentials are absent from account responses.", password_protection)

                def recovery_pair():
                    existing = client.post("/auth/forgot-password", json={"email": b["email"]})
                    missing = client.post("/auth/forgot-password", json={"email": "privacy-missing@example.com"})
                    return existing, missing

                def enumeration():
                    existing, missing = recovery_pair()
                    return existing.status_code == missing.status_code == 200 and existing.json() == missing.json(), {"existing": summary(existing), "missing": summary(missing)}
                run("PR-07", "Account enumeration", "Existing and missing accounts receive identical HTTP 200 response bodies.", enumeration)

                def disclosure():
                    delivery.reset_mock()
                    existing, missing = recovery_pair()
                    private_token = delivery.call_args.args[1] if delivery.called else ""
                    if private_token:
                        secret_values.append(private_token)
                    clean = bool(private_token) and private_token not in existing.text + missing.text and "token" not in existing.json() and "dev_reset_token" not in existing.json()
                    return clean and existing.status_code == missing.status_code == 200, {"existing": summary(existing), "missing": summary(missing), "private_mock_delivery_calls": delivery.call_count, "public_token_absent": clean}
                run("PR-08", "Reset-token confidentiality", "Reset token goes only to mocked private delivery, never the public response.", disclosure)

                def takeover():
                    public = client.post("/auth/forgot-password", json={"email": b["email"]})
                    response = client.post("/auth/reset-password", json={"token": public.json().get("dev_reset_token", "not-available"), "new_password": "SyntheticAttacker123!"})
                    owner = client.post("/auth/login", json={"email": b["email"], "password": b["password"]})
                    return response.status_code == 400 and owner.status_code == 200, {"reset_status": response.status_code, "original_owner_login": owner.status_code}
                run("PR-09", "Unauthorized password reset", "Public requester cannot reset the account; owner's original password still works.", takeover)

                def single_use():
                    user = account("single-use")
                    with SessionLocal() as db:
                        token = create_reset_token(db, db.get(User, user["id"]))
                        secret_values.append(token)
                        stored = db.query(PasswordResetToken).filter_by(token=hashlib.sha256(token.encode()).hexdigest()).one()
                        hashed = stored.token != token
                    first = client.post("/auth/reset-password", json={"token": token, "new_password": "SyntheticReset123!"})
                    second = client.post("/auth/reset-password", json={"token": token, "new_password": "SyntheticReuse123!"})
                    login = client.post("/auth/login", json={"email": user["email"], "password": "SyntheticReset123!"})
                    return hashed and first.status_code == 204 and second.status_code == 400 and login.status_code == 200, {"digest_only_stored": hashed, "first_reset": first.status_code, "reused_token": second.status_code, "new_password_login": login.status_code}
                run("PR-10", "Reset-token hashing and single use", "Only digest stored; first reset succeeds; token reuse fails.", single_use)

                def expiry():
                    user = account("expiry")
                    with SessionLocal() as db:
                        token = create_reset_token(db, db.get(User, user["id"]))
                        secret_values.append(token)
                        row = db.query(PasswordResetToken).filter_by(token=hashlib.sha256(token.encode()).hexdigest()).one()
                        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
                        db.commit()
                    response = client.post("/auth/reset-password", json={"token": token, "new_password": "SyntheticExpired123!"})
                    login = client.post("/auth/login", json={"email": user["email"], "password": user["password"]})
                    return response.status_code == 400 and login.status_code == 200, {"expired_reset": response.status_code, "original_password_login": login.status_code}
                run("PR-11", "Expired reset token", "Expired reset gets 400 and does not change the password.", expiry)

                def revocation():
                    user = account("session")
                    change = client.post("/auth/change-password", headers=user["headers"], json={"current_password": user["password"], "new_password": "SyntheticChanged123!"})
                    old = profile(user["token"])
                    login = client.post("/auth/login", json={"email": user["email"], "password": "SyntheticChanged123!"})
                    new_access = profile(login.json()["access_token"]) if login.status_code == 200 else login
                    return change.status_code == 204 and old.status_code == 401 and login.status_code == new_access.status_code == 200, {"password_change": change.status_code, "old_session": old.status_code, "fresh_login": login.status_code, "fresh_session": new_access.status_code}
                run("PR-12", "Session invalidation after password change", "Old session rejected; fresh login and fresh session succeed.", revocation)

                def suspension():
                    user = account("suspension")
                    initial = profile(user["token"])
                    change = client.patch("/admin/users/" + user["id"], headers=admin["headers"], json={"is_active": False})
                    later = profile(user["token"])
                    return initial.status_code == change.status_code == 200 and later.status_code == 401, {"before_suspension": initial.status_code, "suspend": change.status_code, "after_suspension": later.status_code}
                run("PR-13", "Suspended account session", "Suspension invalidates a previously working session.", suspension)

                def personal_data():
                    query = "Medical dataset email fake.person@example.com phone 000-000-0000"
                    history(a, "healthcare", query)
                    detail = client.get("/admin/users/" + a["id"], headers=admin["headers"])
                    queries = [entry["query"] for entry in detail.json()["search_history"]]
                    prompt = dataset_prompt(query)
                    with SessionLocal() as db:
                        stored = db.execute(text("SELECT query FROM search_history WHERE user_id = :uid"), {"uid": a["id"]}).scalars().all()
                    absent = all("fake.person@example.com" not in value and "000-000-0000" not in value for value in queries + [prompt])
                    encrypted = bool(stored) and all(value.startswith(PREFIX) for value in stored)
                    return detail.status_code == 200 and bool(queries) and absent and encrypted, {"stored_queries_after_redaction": queries, "contact_values_absent_from_history_and_prompt": absent, "raw_search_text_encrypted": encrypted, "scope": "Email/phone patterns only; no claim of comprehensive PII detection."}
                run("PR-14", "Personal-data handling", "Synthetic email/phone absent from history and prompt; raw search text encrypted.", personal_data)

                def deletion():
                    with SessionLocal() as db:
                        a_before = db.query(SearchHistory).filter_by(user_id=a["id"]).count()
                        b_before = db.query(SearchHistory).filter_by(user_id=b["id"]).count()
                    response = client.delete("/recommendations", headers=a["headers"])
                    with SessionLocal() as db:
                        a_after = db.query(SearchHistory).filter_by(user_id=a["id"]).count()
                        b_after = db.query(SearchHistory).filter_by(user_id=b["id"]).count()
                    return response.status_code == 204 and a_before > 0 and a_after == 0 and b_before > 0 and b_before == b_after, {"delete_status": response.status_code, "A_before": a_before, "A_after": a_after, "B_before": b_before, "B_after": b_after}
                run("PR-15", "History deletion isolation", "A deletes its own history while B's existing history stays unchanged.", deletion)
        finally:
            engine.dispose()

    counts = {status: sum(record["outcome"] == status for record in results) for status in ("PASS", "FAIL", "ERROR")}
    unchanged = before == digest()
    manifest = {"executed_at": started.isoformat(), "counts": counts, "original_database_unchanged": unchanged,
                "database_scope": "Temporary synthetic SQLite; no working or hosted database connection.",
                "mail_scope": "Mocked private email delivery. No real SMTP verification.",
                "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in (ROOT / "backend").rglob("*")
                                  if path.is_file() and path.suffix in {".py", ".json"} and "__pycache__" not in path.parts}}
    (output / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("\nGowsika's 15 privacy cases: " + json.dumps(counts), flush=True)
    print("Original database unchanged: " + str(unchanged), flush=True)
    print("Fresh evidence: " + str(output), flush=True)
    return 0 if len(results) == 15 and not counts["FAIL"] and not counts["ERROR"] and unchanged else 1


if __name__ == "__main__":
    sys.exit(main())
