# Team & Module Breakdown — DATA NEBULA AI

Source: `Group Assignment Brief.pdf` (IT3041 – Information Retrieval and Web Analytics)
and `IRWA CHATGPT FULL REPORT.docx`.

> **Also see [`docs/individual-assignment.md`](individual-assignment.md)** — a
> *separate, individually graded* 100-mark assignment (80 report + 20 viva)
> where each member independently red-teams this same system from an assigned
> angle (prompt injection, privacy/data leakage, Responsible AI/bias, or IR
> security) and submits their own vulnerability assessment report. Everyone on
> the team needs to read that file — it's graded per-person, not per-group.

> **Also see `docs/mid-evaluation/`** — three self-contained prep files
> ([`member1-nlp-agent.md`](mid-evaluation/member1-nlp-agent.md),
> [`member2-security-agent.md`](mid-evaluation/member2-security-agent.md),
> [`member3-frontend-ui.md`](mid-evaluation/member3-frontend-ui.md)), one per
> member, each answering all 6 Mid Evaluation discussion points in full plus a
> "your files" section. **Every member should read all three**, not just
> their own — the brief requires everyone to understand the whole system.
> These also propose rebalancing agent ownership 1:1 per member (below).

> **Also see [`docs/agent-improvements.md`](agent-improvements.md)** — a
> running log of real issues found per agent (several via live testing, e.g.
> an actual prompt injection attempt against the NLP Agent) and what was
> fixed vs. left open. Good source material for the report's evaluation
> section and for the individual security assignment above — some open
> items there are exactly what that assignment asks someone to test.

## Project

Multi-agent AI system for natural-language dataset discovery. User describes a need in
plain English → NLP Agent extracts structured intent → an Information Retrieval agent
finds matching datasets → an Evaluation agent ranks/explains results → all served through
a FastAPI gateway to a Next.js frontend.

Assignment hard requirements (from the brief): ≥2 interacting agents, an LLM, NLP
techniques, an Information Retrieval module, security features (auth, input
sanitization, encryption), a defined agent communication protocol, Responsible AI
coverage, and a commercialization plan. Individual contribution is checked at the viva,
so each member's branch/commits should reflect work that member actually did.

## Branches

```
main
 └── dev
      ├── member1-nlp-agent        (NLP/Discovery/Evaluation agents, CORS, architecture)
      ├── member2-security-agent   (auth backend implemented)
      └── member3-frontend-ui      (full UI implemented)
```

> **Resolved — agent ownership rebalanced 1:1 per member.** All 3 core agents
> were originally built on `member1-nlp-agent` as a working foundation (Split B
> from the source report — Member 2 = Security, Member 3 = Frontend — left
> Member 1 with all 3 AI agents, which isn't an equal split of *agent* work
> specifically). Going forward, ownership for explaining, defending, and
> extending each agent is:
> - **Member 1** — NLP Agent + overall architecture/orchestration
> - **Member 2** — Discovery (IR) Agent + Security (still the widest scope,
>   since Discovery and Security are both real, substantial pieces)
> - **Member 3** — Evaluation Agent + Frontend (a natural pairing — the
>   Evaluation Agent's explanations are what the frontend's `ExplanationCard`
>   displays)
>
> This doesn't rewrite what's already built or its git history — it's who
> takes point on each agent from here on (report sections, viva answers,
> future commits). Full detail and reasoning in `docs/mid-evaluation/`.

## Member 1 — NLP + Discovery + Evaluation Agents, Architecture Lead (`member1-nlp-agent`)

**Status: implemented — all 3 core AI agents + orchestrator.** All 3 agents were
built here as the initial working foundation; per the rebalance above, Member 1
now owns the **NLP Agent** specifically going forward, with Discovery going to
Member 2 and Evaluation to Member 3 (they're identical code either way — this
is about who explains/extends/defends which agent from here on).

### NLP Agent — `backend/agents/nlp_agent/`
- `agent.py` — validate → spaCy pipeline (keywords/entities) → Gemini LLM understanding,
  falling back to the rule-based classifier (`config.json`) when no `GEMINI_API_KEY` is
  set or the LLM call fails. `understanding_source` on the response says which path ran
  (`llm` or `rule_based`) — transparency for the Responsible AI section.
- `preprocessing.py` — spaCy model loading, keyword/entity extraction.
- `models.py` — `QueryInput`, `QueryAnalysisResult`.
- `config.json` — domain/task/data-type trigger keywords for the fallback classifier.

### Discovery (IR) Agent — `backend/agents/discovery_agent/`
- `datasets.json` — curated catalog (10 sample entries across the 5 domains).
- `embeddings.py` — `sentence-transformers` (`all-MiniLM-L6-v2`) text embeddings.
- `vector_store.py` — FAISS `IndexFlatL2` semantic search over the catalog.
- `agent.py` — `search_datasets(query, k)`.

### Dataset Collection Agent — `backend/agents/dataset_collection_agent/`
- `kaggle_source.py` — live Kaggle dataset search via the `kaggle` package, scored
  against the query with the same sentence-transformer embeddings as the Discovery
  Agent (cosine similarity). Domain/task are left `"unspecified"` since Kaggle's search
  API doesn't expose that metadata (unlike the curated catalog).
- `agent.py` — `collect_external_datasets(query, limit)`, returns `[]` (not an error)
  when `KAGGLE_API_TOKEN` isn't set or the API call fails — same graceful-fallback
  pattern as the LLM client.
- Results are merged with the catalog's Discovery Agent results before evaluation
  (`main.py::_candidate_datasets`), each tagged with `source: "catalog"` or
  `"kaggle"` for transparency.

**Kaggle auth note:** the guide for setting this up commonly describes the older
`kaggle.json` / `KAGGLE_USERNAME`+`KAGGLE_KEY` scheme. The version installed here
(`kaggle==2.2.4`) uses a different flow: go to
[kaggle.com/settings/api](https://www.kaggle.com/settings/api) → "Generate New Token" →
put the token string in `KAGGLE_API_TOKEN` in the repo-root `.env` (see
`backend/.env.example`). Also note: `kaggle.KaggleApi.authenticate()` calls
`sys.exit(1)` on total auth failure by default — `kaggle_source.py` guards against that
so a bad/missing token can't crash the FastAPI process.

### Evaluation Agent — `backend/agents/evaluation_agent/`
- `scorer.py` — weighted score: similarity + domain match + task match + keyword
  overlap (weights are named constants, not magic numbers).
- `agent.py` — `evaluate_datasets(datasets, requirement)`, sorted by score, each with a
  generated explanation string (Responsible AI explainability).

### LLM client — `backend/llm/`
- `gemini_client.py` — wraps the `google-genai` SDK. Reads `GEMINI_API_KEY` from the
  environment (never hardcode it). Raises `LLMUnavailableError` on a missing key or any
  API error, which `nlp_agent/agent.py` catches to fall back to the rule-based path.
- `prompts.py` — the structured-JSON prompt template.

### Gateway — `backend/main.py`
| Endpoint | Purpose |
|---|---|
| `POST /nlp-agent?query=...` | NLP Agent only |
| `POST /discovery-agent?query=...&k=` | Discovery Agent only (catalog) |
| `POST /dataset-collection-agent?query=...&k=` | Live Kaggle search only |
| `POST /evaluation-agent?query=...&k=` | NLP → Discovery+Kaggle → Evaluation, scores only |
| `POST /discover?query=...&k=` | Full pipeline: understanding + ranked, explained recommendations |

Run it:
```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn main:app --reload
```
`GEMINI_API_KEY` and `KAGGLE_API_TOKEN` (both optional) go in the **repo-root** `.env`,
loaded explicitly regardless of which directory you run uvicorn from. Without them, the
NLP agent uses the rule-based fallback and Discovery only searches the local catalog —
the system is fully functional either way.

**Model note:** newly-created Gemini API keys currently can't access `gemini-2.5-flash`,
`gemini-2.5-pro`, or `gemini-2.5-flash-lite` (Google returns a 404 "no longer available
to new users" even though those models are listed). `gemini-3.5-flash` works and is set
as the default (`llm/gemini_client.py`, override with the `GEMINI_MODEL` env var). If
Google changes this again, run `client.models.list()` to see what your key can access.

Test at `http://localhost:8000/docs`, or:
```bash
curl -X POST "http://localhost:8000/discover?query=I%20need%20datasets%20for%20predicting%20diabetes"
```
Verified live against the real Gemini API on 2026-08-16 — `understanding_source: "llm"`
in the response confirms the LLM path (not the fallback) is running.

**Note on the "agent communication protocol" requirement:** the three agents currently
communicate via direct Python function calls inside one FastAPI process (structured
Pydantic messages between them). This is a legitimate multi-agent design, but if you
want a literal separate-process HTTP protocol for extra marks/viva depth, the Discovery
Agent can be split out and run as its own service (the source report's Step 6 shows this:
`uvicorn agents.discovery_agent.api:app --port 8001`) with the gateway calling it over
HTTP instead of importing it directly. Optional — not done here to keep initial scope
manageable.

## Member 2 — Security Agent + Responsible AI (`member2-security-agent`)

**Status: auth is implemented and live; Responsible AI + input sanitization
are still open.** See `backend/security/README.md` for the exact file-by-file
status and the full `/auth/*` API reference. Summary:

- **Done** — `db.py`/`db_models.py` (SQLite via SQLAlchemy), `jwt_manager.py`
  (PyJWT), `authentication.py` (bcrypt + `get_current_user` dependency),
  `password_reset.py`, `schemas.py`, `router.py`. Register/login/profile
  update/change-password/forgot-password/reset-password all work and are
  verified end-to-end (see commit history on `member2-security-agent`).
- **Open** — `input_filter.py` (prompt-injection filtering in front of the
  NLP agent's LLM calls — nothing sanitizes user queries before they reach
  Gemini right now), `encryption.py` (not yet needed — nothing sensitive
  beyond password hashes is stored), `responsible_ai/{fairness,explainability,privacy}.py`
  (the Evaluation Agent already generates its own explanation strings;
  these would add a dedicated bias/fairness angle on top).
- `docs/security.md` for the report is still to be written.

## Member 3 — Frontend + UX (`member3-frontend-ui`)

**Status: implemented.** Real components, not stubs — see
`frontend/dataset-ai-ui/components/README.md` for the file-by-file status.
Space-themed UI (3D starfield via `@react-three/fiber`, glassmorphism,
framer-motion), search wired to `POST /discover`, agent-pipeline
visualization, dataset result cards, and the full auth UI (login, register,
forgot/reset password, profile) plus a pricing page for the
commercialization section. Nothing left stubbed on the frontend.

## Deliverables checklist (from the brief)

- [ ] Mid Evaluation demo (Week 6): architecture, agent roles, comms flow, progress demo, Responsible AI check, commercialization pitch.
- [ ] Gen AI video (3–5 min, Week 10).
- [ ] Final report using the provided template: design, methodology, Responsible AI, commercialization + pricing, evaluation results.
- [ ] GitHub repo with clear README (setup, usage, contributors).
- [ ] Viva prep per member (see report for suggested Q&A per role).

## Workflow

Each member works on their own branch, commits their own work with their own GitHub
account, opens a PR into `dev`, and the team reviews/merges. `dev` merges into `main`
once integrated and tested.
