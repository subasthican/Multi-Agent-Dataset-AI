# Discovery Agent — Gowsika
## Verified application fixes — 5 October 2026

The original assessment findings are retained as baseline evidence. The fixes were implemented at the user's request and **all 69 application retests passed**, with a separate passing, idempotent migration check. See [fix verification](fix-verification/README.md) for outcomes, evidence and limitations.

- **Subasthican:** input guards, untrusted-input prompt framing, strict model-output schema and safe fallback. Fifteen original attack inputs are rejected before provider invocation; fifteen controlled malformed outputs are handled safely. Live Gemini resistance remains unverified because the provider rejects the existing key.
- **Gowsika:** private reset-email flow, reset-token digests and single-use handling, password-change/recovery session invalidation, contact redaction, independent atomic usage counters, quotas on standalone routes HTTP(S) catalog URL validation, transactional admin audit logs and password confirmation with failed-attempt throttling for deletions, plus authenticated encryption and migration of stored search text. SMTP delivery needs local configuration; tests mock delivery.
- **Kageepan:** specific intent precedence, language/unsupported-domain warnings, modality metadata and filtering, consistent normalized similarity, discriminatory-request guards, clearer heuristic score/privacy disclosures and frontend recovery/session updates.

Student IDs, lecturer-confirmed specializations and each member's own reflection are deferred as requested. Draft notes and viva practice material are provided; they do not certify independent student work or a completed viva. These finite checks do not establish 100% system security or assessment completion.


> **Your two responsibilities:** group work = Discovery Agent + security; proposed individual audit = **Privacy and Data Leakage Assessment**. The individual work is an independent security/Responsible AI assessment, not another agent implementation. See the individual assignment section below.

Location: [`backend/agents/discovery_agent/`](../backend/agents/discovery_agent/)

## What this agent is

The Discovery Agent is the **second stage** of the pipeline — the actual Information
Retrieval (IR) component the assignment requires. It takes the structured understanding
the NLP Agent produced (domain, task, keywords) and uses it to **find candidate
datasets** from a curated local catalog, returning them ranked by semantic similarity to
the original query.

This is not keyword/SQL matching — it uses vector embeddings and FAISS squared-L2 distance for local retrieval, i.e. it understands that a query about "predicting patient risk" and a
dataset described as "clinical records for disease diagnosis" are related even though
they don't share exact words.

## Why it's needed

The NLP Agent only understands what the user *wants*; it has no idea what datasets
actually *exist*. The Discovery Agent is the bridge between "what the user is asking
for" and "what's actually in the catalog" — it's the search/retrieval engine of the
system, and it's what makes this an Information Retrieval project rather than just an
NLP one.

## How it retrieves datasets (the IR technique used)

1. Every dataset in the catalog has its `description` turned into a numeric vector
   (an embedding) using a sentence-transformer model (`all-MiniLM-L6-v2`).
2. These vectors are loaded into a FAISS index (`IndexFlatL2`) — a library built
   specifically for fast similarity search over vectors, from Facebook AI Research.
3. The user's query is embedded the same way, and FAISS returns the `k` closest
   datasets by distance in that vector space.
4. That raw distance is converted to a 0–1 similarity score
   (`similarity = 1 / (1 + distance)`) so a higher number always means "more similar,"
   which is what the Evaluation Agent expects.

This whole approach means dataset matching is based on **meaning**, not exact keyword
overlap — which is the actual point of using embeddings instead of a plain text search.

## Files this agent needs, and what each one means

### `agent.py` — the entry point
A small, deliberately thin file. `search_datasets(query, k)` is the one function the
rest of the system calls: it runs the vector search (`vector_store.py`) and wraps the
raw dict results into validated `DatasetMatch` objects (`models.py`), returning a
`DiscoveryResult`. Kept thin on purpose — all the actual retrieval logic lives in
`vector_store.py` so this file's only job is "call the search, validate the shape."

### `vector_store.py` — the actual retrieval engine
This is where the IR technique described above is implemented:
- `load_datasets()` — pulls every row from the `catalog_datasets` table in the database
  (not a static file — this catalog is admin-editable) and caches it in memory, since
  hitting the database on every single search would be wasteful.
- `build_index()` — turns every dataset's description into an embedding (via
  `embeddings.py`) and builds the FAISS index from them, also cached.
- `invalidate_cache()` — clears both caches. This gets called whenever an admin
  adds/edits/deletes a catalog entry, so a change to the catalog shows up in search
  results immediately instead of only after a server restart.
- `search_vectors(query, k)` — embeds the query, asks FAISS for the `k` nearest
  datasets, and returns them with a computed similarity score attached.

### `embeddings.py` — turning text into vectors
Wraps the `sentence-transformers` library:
- `get_embedding_model()` — loads the `all-MiniLM-L6-v2` model once and caches it
  (loading a transformer model on every request would be far too slow).
- `create_embeddings(texts)` — turns a list of strings into a list of numeric vectors.
- `rank_by_similarity(query, texts)` — computes cosine similarity between the query and
  a list of texts, used specifically by the external dataset sources (Kaggle, OpenML,
  HuggingFace collection agent) to score external matches on a 0–1 scale. Local retrieval uses `1 / (1 + squared-L2 distance)`;
  sharing a range does not make these scores equivalent or calibrated.

### `models.py` — the data contracts
Pydantic schemas defining every shape this agent deals with:
- `DatasetMatch` — one retrieved dataset: `id`, `name`, `domain`, `task`, `description`,
  `similarity`, `source` (which platform it came from — `catalog`, `kaggle`, `openml`,
  or `huggingface`), and an optional `url` (a real clickable link to the dataset's page,
  left `null` rather than ever being invented for a catalog entry that has no real page).
- `DiscoveryResult` — the full response: the original `query` plus its list of
  `matches`.
- `CatalogDatasetCreate` / `CatalogDatasetUpdate` / `CatalogDatasetResponse` — the
  schemas used by the admin panel to add, edit, and list catalog entries (`name`,
  `description`, `domain`, `task`, optional `url`).

### `seed.py` — first-run catalog setup
`seed_catalog_if_empty()` runs once at server startup. It checks whether the
`catalog_datasets` database table already has any rows; if it's completely empty (i.e.
this is the very first run, or every seed entry was deliberately deleted), it loads
`datasets.json` and inserts those as the starting catalog. If the table already has data
— including an admin having removed some seed entries on purpose — this does nothing, so
partial edits are preserved. Deleting every entry causes startup to reseed the catalog.

### `datasets.json` — the starting catalog data
A plain JSON array of the 10 original curated dataset entries (name, description,
domain, task) used only to seed the database the very first time the app runs. After
that first run, the database — not this file — is the real source of truth; the admin
panel edits the database directly, and this file is never read again unless the catalog
table is completely emptied.

## Summary of the flow

```
QueryAnalysisResult (from NLP Agent)
   →  embed the query (embeddings.py)
   →  FAISS similarity search over embedded catalog descriptions (vector_store.py)
   →  DatasetMatch objects with a similarity score (agent.py, models.py)
   →  DiscoveryResult  →  passed to the Evaluation Agent
```

## Individual assignment — Gowsika

**Proposed specialization: Privacy and Data Leakage Assessment. Lecturer confirmation pending.**

### Recorded assessment and remaining work

An AI-assisted draft with actual results, evidence, findings, risk matrix and mitigations is available in [your assessment report](individual-assessments/gowsika-privacy-assessment.md). See the [assessment summary](individual-assessments/README.md) for scope and reproduction steps. Lecturer allocation, independent student reproduction, personal reflection and final submission remain pending.

Recorded primary cases: **10 PASS, 5 FAIL, 0 BLOCKED**. A FAIL records a failed criterion, not an unexecuted test.

### Components and current observations to investigate

- `backend/security/authentication.py`, `jwt_manager.py`, `router.py`, `password_reset.py`, `schemas.py`, `db_models.py`, `admin_router.py`.
- `backend/agents/recommendation_agent/agent.py`, `backend/main.py`, `backend/responsible_ai/privacy.py`.
- Frontend `services/api.ts`, `contexts/AuthContext.tsx`, profile/reset pages; the SQLite test database.

Use controlled accounts A and B plus an admin test account. Signed-in raw queries are stored, admins can view history, and Gemini receives queries when enabled. Anonymous queries are not deliberately persisted by application history logic, but query-string transport and infrastructure/provider handling must be considered. Reset tokens are currently returned by the public forgot-password API. Old JWTs are not explicitly revoked by password changes. Validate these observations through tests; do not mark them as executed evidence.

### Minimum 15-test plan

Status reflects the **AI-assisted assessment run**. PASS/FAIL are executed observations; BLOCKED means evaluation could not complete. Each student must independently reproduce and validate their cases. Expected behavior is the criterion, not a claim about current behavior.

| Test ID | Objective | Input / scenario | Expected behavior / criterion | Recorded outcome | Evidence |
|---|---|---|---|---|---|
| PR-01 | Unauthenticated profile access | Call GET /auth/me without a token. | 401; no profile data. | PASS | [Log](individual-assessments/evidence/PR-01.json) |
| PR-02 | Tampered JWT | Modify a controlled JWT and request /auth/me. | 401; no data. | PASS | [Log](individual-assessments/evidence/PR-02.json) |
| PR-03 | Expired JWT | Use an expired controlled token on a protected route. | 401; no data. | PASS | [Log](individual-assessments/evidence/PR-03.json) |
| PR-04 | Cross-user history access | As A, attempt GET /admin/users/{B_id}; also inspect A’s /recommendations. | Non-admin denied; recommendations must use only A’s history. | PASS | [Log](individual-assessments/evidence/PR-04.json) |
| PR-05 | Normal-user admin access | Call /admin/users and /admin/stats as a normal user. | 403; no administrative user data. | PASS | [Log](individual-assessments/evidence/PR-05.json) |
| PR-06 | Password-hash exposure | Inspect registration, login, profile and admin response bodies. | No raw passwords or hashes returned. | PASS | [Log](individual-assessments/evidence/PR-06.json) |
| PR-07 | Account enumeration | Compare registration/reset responses for existing and nonexistent controlled emails. | Document whether responses disclose account existence. | FAIL | [Log](individual-assessments/evidence/PR-07.json) |
| PR-08 | Reset-token disclosure | Call forgot-password for controlled account B without authentication. | No usable token disclosed to an unauthenticated requester. | FAIL | [Log](individual-assessments/evidence/PR-08.json) |
| PR-09 | Reset without email ownership | Using only B’s known test email, attempt the reset flow and verify a controlled login. | Ownership proof required; unrelated requester cannot reset B. | FAIL | [Log](individual-assessments/evidence/PR-09.json) |
| PR-10 | Reset-token reuse | Consume a controlled token then try to consume it again. | Second attempt rejected; password unchanged by reuse. | PASS | [Log](individual-assessments/evidence/PR-10.json) |
| PR-11 | Expired reset token | Attempt reset using an expired token in the isolated test environment. | Rejected; password unchanged. | PASS | [Log](individual-assessments/evidence/PR-11.json) |
| PR-12 | JWT after password change | Save A’s JWT, change A’s password, then retry the saved JWT. | Assess whether compromised sessions remain usable; record policy and result. | FAIL | [Log](individual-assessments/evidence/PR-12.json) |
| PR-13 | Suspended-account JWT | Suspend B using the admin, then retry B’s existing JWT on /auth/me. | Protected access rejected immediately. | PASS | [Log](individual-assessments/evidence/PR-13.json) |
| PR-14 | Synthetic PII handling | Search while signed in using fake email/phone details; inspect permitted DB/admin views and provider-bound request construction. | Document storage, disclosure, redaction and protection; do not assume consent or compliance. | FAIL | [Log](individual-assessments/evidence/PR-14.json) |
| PR-15 | History deletion | Create A/B history, clear A via DELETE /recommendations, inspect DB/admin views and recommendations. | A’s history removed; B’s history preserved. | PASS | [Log](individual-assessments/evidence/PR-15.json) |

### What you must do independently

1. Confirm your specialization with the lecturer. The mapping here is a team proposal, not a confirmed lecturer allocation. The fourth specialization (Information Retrieval and Security) is unassigned in this three-member proposal; the lecturer determines how it applies.
2. Read the full system architecture, not only your own agent. Review [the individual brief](Individual%20Assignment%20Brief.pdf), [the group brief](Group%20Assignment%20Brief.pdf), and [the team overview](members.md).
3. Record the tested Git commit, date, operating environment, dependencies, model/configuration, test accounts, and relevant limitations. Use a local test database and synthetic personal information. Keep real credentials and personal data out of submitted evidence.
4. Execute at least 15 independent cases in your assigned specialization. The table links recorded AI-assisted evidence. It does not establish independent student execution. A suggested test or code-review observation without runtime evidence is not a completed test.
5. Capture the exact input, HTTP status/response, relevant UI screenshot or log, and observations. For comparisons, record each input and response separately. Reproduce failures and identify the affected code.
6. Classify each supported finding as Critical, High, Medium, Low, or Informational, explaining impact, likelihood, technical cause, and the reason for its severity. Passing tests also count when properly documented; do not invent vulnerabilities.
7. Recommend practical mitigations. The individual brief asks for assessment of the existing system, not redesign. Record the baseline before fixes; if retesting a fix, identify its separate commit and result.
8. Write your own report and prepare to defend your methodology, why attacks succeeded/failed, risk ratings, mitigations, and Responsible AI implications in the individual viva.

### Evidence template — repeat for every completed case

```text
Test ID:
Objective:
Environment / commit / model / account role:
Input or attack scenario and steps:
Expected behavior:
Actual behavior: PENDING
Evidence file or log reference: PENDING
Observations: PENDING
Conclusion / outcome: PENDING
Related vulnerability ID (if any):
```

Include observations and a conclusion as well as the required objective, input, expected/actual behavior, and evidence. An unavailable dependency or inaccessible live model must be recorded as a limitation or blocked case, not a pass.

### Your independent report checklist

- [ ] Executive Summary: objectives and supported major findings.
- [ ] Scope of Testing: system, specialization, components, exclusions and limitations.
- [ ] Evaluation Methodology: approach, tools, environment, process and criteria.
- [ ] Test Cases Performed: 15+ independent cases with IDs, objectives, inputs, expected/actual results, evidence and outcomes.
- [ ] Vulnerabilities Identified: description, evidence, impact, likelihood, severity, risk level and technical explanation for each finding.
- [ ] Risk Assessment: a vulnerability × impact × likelihood × risk-level matrix with a defined rating method.
- [ ] Mitigation Strategies: practical recommendations tied to each finding.
- [ ] Reflection: challenges, lessons and future improvements.
- [ ] Individual viva preparation: explain and justify your own tests and findings.

The report is worth **80 marks** and the individual viva **20 marks**. Three members need three independently authored reports and at least **45 executed tests overall**, assuming the lecturer assigns these three specializations. This member guide and the linked AI-assisted assessment draft do not certify independent individual-assignment completion.
