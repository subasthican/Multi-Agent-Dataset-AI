# Mid Evaluation Prep — Member 2 (Discovery Agent + Security)

For the Week 6/7 Mid Evaluation: a 15-minute discussion, no slides, 20 marks. The
lecturer is checking **understanding of the plan**, not how much is built. You are
not expected to have a working system yet, but you must be able to explain and
justify every decision below — including the parts you didn't personally write.

> Read this whole file even though it's "your" file — the brief is explicit that
> **every member must be ready to answer all 6 questions**, not just their own
> section. [`member1-nlp-agent.md`](member1-nlp-agent.md) and
> [`member3-frontend-ui.md`](member3-frontend-ui.md) have the same 6 answers with
> a different "your files" section — read those too before the evaluation.

## Your files

| Path | What it is |
|---|---|
| `backend/agents/discovery_agent/agent.py` | `search_datasets(query, k)` — the Discovery Agent's entry point |
| `backend/agents/discovery_agent/vector_store.py` | FAISS index build/search over the catalog |
| `backend/agents/discovery_agent/embeddings.py` | Sentence-transformer embedding model wrapper |
| `backend/agents/discovery_agent/datasets.json` | The curated dataset catalog (10 sample entries) |
| `backend/agents/discovery_agent/models.py` | `DatasetMatch`, `DiscoveryResult` schemas |
| `backend/agents/dataset_collection_agent/` | Live Kaggle search, merged in alongside the catalog results |
| `backend/security/authentication.py`, `jwt_manager.py`, `db.py`, `db_models.py`, `password_reset.py`, `router.py`, `schemas.py` | The whole auth system: register/login, JWT, bcrypt hashing, password reset |
| `backend/security/input_filter.py`, `encryption.py` | **Not yet implemented** — prompt-injection filtering and field encryption, still open |
| `backend/responsible_ai/*.py` | **Not yet implemented** — dedicated fairness/explainability/privacy modules beyond what's already built into the agents |

You have the widest file ownership in the group — the actual Information
Retrieval agent *and* the whole security layer. Be ready to explain both.

---

## 1. Why we selected this domain

**The problem:** ML students, researchers, and independent practitioners
regularly need to find a suitable dataset before they can even start a project,
and the standard way to do it — manually searching Kaggle, OpenML, HuggingFace,
or Google Dataset Search with keyword queries — is slow and imprecise. These
platforms match on titles/tags, not on what the person actually means. A query
like *"I need data for predicting diabetes"* doesn't reliably surface the right
datasets unless you already know the exact terminology used on that platform.

**Why it matters:** Dataset discovery is widely recognized as one of the most
time-consuming, least-supported stages of the ML workflow — it happens before
any modeling work, and a poor dataset choice quietly wastes days of downstream
effort. Cutting this search time down has real value for anyone doing applied ML.

**Who experiences it:** Students working on coursework/projects, academic
researchers exploring a new domain, and small teams/startups without a
dedicated data engineering function.

**Why Agentic AI fits:** This isn't a single-step problem. It needs (1)
understanding an unstructured, ambiguous natural-language request, (2)
semantic — not keyword — search across a large space of candidate datasets,
and (3) reasoning about *why* a result is a good match and ranking accordingly.
Each of those is a distinct kind of reasoning, which is exactly what agentic
decomposition is for: specialized agents, each responsible for one step,
communicating through a defined pipeline, rather than one monolithic model
trying to do everything at once.

## 2. Our proposed system — DATA NEBULA AI

A multi-agent system where a user describes what they need in plain English and
gets back **ranked, explained dataset recommendations** pulled from both a
curated catalog and live Kaggle search.

- **Problem it solves:** removes the manual, multi-platform, keyword-guessing
  search process.
- **Target users:** ML students, researchers, independent practitioners, small
  teams without dedicated data infrastructure.
- **What it does:** takes a natural-language query → understands the intent
  (domain, task, data type, keywords) → searches a dataset catalog and live
  Kaggle results semantically → scores and ranks candidates → explains *why*
  each one was recommended.
- **Value:** faster discovery, lower expertise bar (you don't need to know
  platform-specific search syntax), and transparent reasoning instead of a
  black-box ranked list.

## 3. Agents and their roles

Three agents, each a distinct reasoning step, chained into one pipeline:

1. **NLP Agent** (Member 1) — converts the raw query into structured intent:
   `domain`, `task`, `data_type`, `keywords`, using an LLM with a rule-based
   fallback. *Necessary because* nothing downstream can search meaningfully
   without first turning free text into structured fields.

2. **Discovery Agent** (mine) — takes the structured intent and finds
   candidate datasets two ways: (a) semantic search over a curated catalog —
   dataset descriptions are embedded with a sentence-transformer model and
   compared against the query embedding via FAISS similarity search, and (b)
   a live call to Kaggle's search API for real, up-to-date datasets, scored
   with the same embedding model for a comparable relevance signal.
   *Necessary because* this is the actual information retrieval step — where
   the candidate datasets come from and how "relevant" gets defined
   mathematically rather than by keyword match.

3. **Evaluation Agent** (Member 3) — scores and ranks what the Discovery
   Agent returns, and explains each recommendation in plain language.
   *Necessary because* a similarity score alone doesn't tell a user *why*
   something matched, or let them compare candidates against domain/task fit
   specifically.

**Communication:** the three agents are chained through the FastAPI
orchestrator (`POST /discover`) using typed Pydantic schemas — my Discovery
Agent receives the NLP Agent's `QueryAnalysisResult`-derived query string and
returns a list of `DatasetMatch` objects, which the Evaluation Agent scores.
Currently in-process function calls; could be split into an independently
deployed service reachable over HTTP without changing that interface, if we
want to demonstrate literal inter-process agent communication.

**Collectively:** query in, structured understanding, semantic retrieval,
ranked and explained results out — three narrow specialists producing one
coherent answer none of them could produce alone.

## 4. Implementation plan

- **Backend:** Python, FastAPI as the gateway/orchestrator.
- **LLM:** Google Gemini via `google-genai`, with a rule-based fallback.
- **NLP:** spaCy for tokenization/keyword/entity extraction.
- **Information Retrieval (mine):** `sentence-transformers` embeddings +
  FAISS `IndexFlatL2` for semantic similarity over the local catalog; the
  `kaggle` Python package for live search, scored with the same embedding
  model via cosine similarity so both sources are comparable. Domain/task
  metadata is only available for the curated catalog — Kaggle results are
  tagged `"unspecified"` for those fields, an honest limitation of the live
  source rather than something papered over.
- **Security (mine):** JWT-based auth (`pyjwt`), bcrypt password hashing,
  SQLite via SQLAlchemy for user storage, single-use time-limited password
  reset tokens. Input sanitization against prompt injection into the LLM step
  and field-level encryption are planned but not yet implemented — real,
  disclosed gaps, not hidden ones.
- **Agent communication:** typed Pydantic schemas through a FastAPI
  orchestrator today; documented path to HTTP-based inter-service
  communication if needed.
- **Frontend:** Next.js, calling the backend's REST API, including the
  login/register/profile pages that consume my auth endpoints.
- **Testing plan:** manual endpoint verification now; before final
  submission, dedicated tests for retrieval relevance (does a domain-specific
  query actually rank domain-matching datasets highest) and for the auth
  flows (register/login/reset, including token expiry and single-use
  enforcement).
- **Deployment plan:** containerize backend and frontend (Docker), deploy to
  a small cloud host for the final demo; not required for Mid Evaluation.

## 5. Responsible AI plan

- **Transparency:** every dataset result is tagged with its `source`
  (`"catalog"` or `"kaggle"`) so users know whether a recommendation came from
  our curated, vetted list or an unreviewed live search result.
- **Explainability:** the Evaluation Agent explains every ranked result in
  plain language rather than showing a bare score.
- **Fairness:** the retrieval catalog currently covers 5 domains with 10
  sample entries — intentionally small and reviewable rather than large and
  unaudited; expanding it (or the live Kaggle source) needs the same scrutiny
  so results don't systematically favor better-represented domains.
- **Privacy (mine):** passwords are bcrypt-hashed and never returned by any
  endpoint; no queries are logged or stored anywhere. The password-reset flow
  currently has no email provider configured, so it returns the reset token
  directly in the API response for development — a deliberate, disclosed
  simplification that would need replacing with real email delivery before
  any real deployment, since anyone who can see that response can reset the
  account.
- **Security (mine):** authentication protects account endpoints; dataset
  search itself stays open by design (see commercialization). Prompt
  injection into the LLM step isn't sanitized yet — a known gap, and
  specifically relevant to my individual security audit assignment
  (`docs/individual-assignment.md`), where this exact system will be
  red-teamed by the team.
- **Misuse/domain risk:** we can't vouch for the quality of externally
  sourced (Kaggle) datasets — tagging their source is the current mitigation,
  encouraging users to do their own due diligence on anything not from the
  curated catalog.

## 6. Commercialization plan

- **Who'd use it:** ML students and researchers (free tier — low willingness
  to pay, high volume), independent practitioners and small research teams
  who search often (paid tier — time saved has direct value), and
  labs/companies wanting private dataset integration (enterprise tier).
- **Value proposition:** faster, more precise dataset discovery than manual
  multi-platform search, with transparent reasoning instead of a black box.
- **Pricing/revenue model:** freemium — Free (catalog + basic Kaggle search),
  Pro (~$19/month — priority LLM access, multi-source discovery, unlimited
  use), Enterprise (custom — private datasets, team seats, API access, SLA).
  Live at `/pricing` in the frontend; note the account system (`plan` field)
  exists but isn't yet wired to real billing — worth being upfront about if
  asked how "done" this is.
- **Deployment/go-to-market:** cloud-hosted SaaS, initial adoption through
  university/research-community channels, expanding to small ML teams once
  there's traction.
