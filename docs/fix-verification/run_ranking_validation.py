"""Reproducible NLP + real MiniLM/FAISS + evaluator catalog validation.

Only provider generation is replaced by an explicit unavailable fixture.
Labels are project-authored; this is not an independent relevance benchmark.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[2]
CASES = Path(__file__).with_name("ranking-cases.json")
DATABASE = ROOT / "database/app.db"
before = hashlib.sha256(DATABASE.read_bytes()).hexdigest()

with tempfile.TemporaryDirectory(prefix="nebula-ranking-") as directory:
    os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(directory) / "validation.db")
    os.environ["DATA_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
    sys.path.insert(0, str(ROOT / "backend"))
    import main
    from agents.nlp_agent import agent as nlp
    from llm.gemini_client import LLMUnavailableError
    from agents.discovery_agent.agent import search_datasets
    from agents.evaluation_agent.agent import evaluate_datasets

    main.on_startup()
    spec = json.loads(CASES.read_text())
    results = []
    with patch.object(nlp, "generate_response", side_effect=LLMUnavailableError("Declared offline validation fixture")):
        for case in spec["cases"]:
            analysis = nlp.analyze_query(case["query"])
            matches = search_datasets(main._discovery_query(analysis), k=10).matches
            ranked = evaluate_datasets(matches, analysis)
            names = [row.dataset.name for row in ranked]
            expected = case["expected_top"]
            rank = names.index(expected) + 1 if expected in names else None
            top_correct = (names[0] if names else None) == expected
            intent_correct = (analysis.domain, analysis.task, analysis.data_type) == (
                case["expected_domain"], case["expected_task"], case["expected_data_type"])
            results.append({**case, "outcome": "PASS" if top_correct and intent_correct else "FAIL",
                            "actual_intent": {"domain": analysis.domain, "task": analysis.task, "data_type": analysis.data_type},
                            "ranked_names": names, "expected_rank": rank,
                            "scores": [row.score for row in ranked]})

positive = [row for row in results if row["expected_top"] is not None]
negative = [row for row in results if row["expected_top"] is None]
count = len(positive)
metrics = {
    "positive_queries": count, "abstention_queries": len(negative),
    "top1_accuracy": sum(row["expected_rank"] == 1 for row in positive) / count,
    "mrr_at_3": sum(1 / row["expected_rank"] if row["expected_rank"] and row["expected_rank"] <= 3 else 0 for row in positive) / count,
    "recall_at_3": sum(bool(row["expected_rank"] and row["expected_rank"] <= 3) for row in positive) / count,
    "ndcg_at_3_single_target": sum(1 / math.log2(row["expected_rank"] + 1) if row["expected_rank"] and row["expected_rank"] <= 3 else 0 for row in positive) / count,
    "abstention_accuracy": sum(not row["ranked_names"] for row in negative) / len(negative),
}
unchanged = before == hashlib.sha256(DATABASE.read_bytes()).hexdigest()
report = {"checked_at": datetime.now(ZoneInfo("Asia/Colombo")).isoformat(), "scope": spec["scope"],
          "labels_sha256": hashlib.sha256(CASES.read_bytes()).hexdigest(),
          "counts": {s: sum(row["outcome"] == s for row in results) for s in ("PASS", "FAIL")},
          "metrics": metrics, "cases": results, "working_database_unchanged": unchanged,
          "limitations": "Metrics apply only to these authored catalog queries. Single-target labels do not measure every returned card's relevance, calibration, external source quality, or population fairness."}
(ROOT / "docs/fix-verification/evidence/ranking-validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"counts": report["counts"], "metrics": metrics, "failures": [r for r in results if r["outcome"] != "PASS"], "working_database_unchanged": unchanged}), flush=True)
sys.exit(0 if unchanged and not report["counts"]["FAIL"] else 1)
