# Individual Assessments — Evidence and Draft Reports

These are AI-assisted assessments of the existing baseline, not claims of independent student completion. Lecturer specialization allocation remains pending. Each student must reproduce their tests, review the findings, author their own reflection/report, and follow course rules for AI assistance. Subasthican’s 30 entries comprise 15 blocked live prompt attempts plus 15 completed controlled output-boundary tests; these are explicitly different execution modes. Original baseline evidence is preserved here. Implemented fixes and 69 passing retests are documented in [fix verification](../fix-verification/README.md).

| Member | Proposed scope | PASS | FAIL | BLOCKED | Report |
|---|---|---|---|---|---|
| Gowsika | Privacy and Data Leakage Assessment | 10 | 5 | 0 | [Draft](gowsika-privacy-assessment.md) |
| Subasthican | Prompt Injection and Jailbreak Analysis | 2 | 13 | 15 | [Draft](subasthican-prompt-assessment.md) |
| Kageepan | Responsible AI and Bias Assessment | 11 | 4 | 0 | [Draft](kageepan-responsible-ai-assessment.md) |

A FAIL is a documented failed criterion, not an unfinished execution. A BLOCKED case is incomplete evaluation. A PASS applies only to the tested criterion/configuration. JSON logs are the evidence; no UI screenshots are claimed. Drafts contain all eight report sections, scenario-level actual results, findings/risk matrix and recommendations; personal reflection and student validation remain pending.

## Reproduce

From the repository root, create an isolated Python environment and install `backend/requirements.txt` plus `httpx`, then install the `en_core_web_sm` spaCy model. This run recovered dependencies from cache; Kaggle was not installed because it is lazy-loaded and no live external-source cases were run. All dependencies actually used passed `pip check`. Configure the project’s existing `.env` Gemini key/model for live prompt cases. Never publish that file.

```bash
python docs/fix-verification/run_retests.py
python docs/individual-assessments/write_reports.py
```

The runner sets a temporary database and random test-only JWT secret before importing the backend. It uses controlled accounts, invokes actual routes/components, writes redacted JSON evidence, checks the original database checksum, and deletes test storage at completion. Baseline runners refuse to overwrite the archived evidence. The fix runner writes separate verification logs. Only test data is sent in live prompt calls. Responsible AI cases use local seeded catalog and forced rule-based understanding; privacy PII test does not send its fake identifiers externally.

Recorded environment and exact package versions: [manifest](evidence/manifest.json), [dependency snapshot](evidence/requirements-lock.txt). Full case data: [results](evidence/results.json). Each report links to individual JSON files.
