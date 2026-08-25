# Mid Evaluation Prep — Member 1 (NLP Agent + Architecture)

For the Week 6/7 Mid Evaluation: a 15-minute discussion, no slides, 20 marks. The
lecturer is checking **understanding of the plan**, not how much is built. You are
not expected to have a working system yet, but you must be able to explain and
justify every decision below — including the parts you didn't personally write.

> Read this whole file even though it's "your" file — the brief is explicit that
> **every member must be ready to answer all 6 questions**, not just their own
> section. [`member2-security-agent.md`](member2-security-agent.md) and
> [`member3-frontend-ui.md`](member3-frontend-ui.md) have the same 6 answers with
> a different "your files" section — read those too before the evaluation.

## Your files

| Path | What it is |
|---|---|
| `backend/agents/nlp_agent/agent.py` | Query understanding: validates input → spaCy pipeline → Gemini LLM (primary) → rule-based fallback (`config.json`) if the LLM is unavailable |
| `backend/agents/nlp_agent/preprocessing.py` | spaCy model loading, keyword/entity extraction |
| `backend/agents/nlp_agent/models.py` | `QueryInput`, `QueryAnalysisResult` schemas |
| `backend/agents/nlp_agent/config.json` | Domain/task/data-type keyword rules for the fallback classifier |
| `backend/llm/gemini_client.py`, `backend/llm/prompts.py` | Gemini API wrapper + the structured-JSON prompt |
| `backend/main.py` | FastAPI gateway — wires all agents into the `/discover` pipeline, CORS |

Going forward, you're also the one who best understands the **overall
architecture and orchestration** (`main.py`), since you built the pipeline that
connects everyone's agent together — be ready to explain how the whole system
fits, not just the NLP piece.

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

1. **NLP Agent** (mine) — converts the raw query into structured intent:
   `domain`, `task`, `data_type`, `keywords`. Uses Gemini (LLM) as the primary
   path for richer understanding, and falls back to a deterministic spaCy +
   keyword-rule classifier if the LLM is unavailable, so the system never
   fully breaks. *Necessary because* nothing downstream can search
   meaningfully without first turning free text into structured fields.

2. **Discovery Agent** (Member 2, alongside Security) — takes the structured
   intent and finds candidate datasets: semantic search over a curated catalog
   via sentence-transformer embeddings + FAISS, plus live results from
   Kaggle's search API. *Necessary because* this is the actual information
   retrieval step — where the datasets come from.

3. **Evaluation Agent** (Member 3, alongside Frontend) — takes the candidate
   datasets and scores/ranks them (semantic similarity + domain/task/keyword
   match), and generates a plain-language explanation for each
   recommendation. *Necessary because* a raw similarity-ranked list isn't
   enough — a user needs to know *why* something was recommended to trust it.

**Communication:** the three agents are chained through my orchestrator in
`backend/main.py` (`POST /discover`), passing typed Pydantic objects between
each step — NLP Agent's `QueryAnalysisResult` becomes the Discovery Agent's
search input, whose `DatasetMatch` list becomes the Evaluation Agent's scoring
input. This is a structured, well-defined agent communication protocol even
though it currently runs in-process; the natural extension (if we want to
demonstrate literal inter-process communication) is splitting the Discovery
Agent into its own service reachable over HTTP, which the architecture already
supports without changing its interface.

**Collectively:** query in, structured understanding, semantic retrieval,
ranked and explained results out — three narrow specialists producing one
coherent answer none of them could produce alone.

## 4. Implementation plan

- **Backend:** Python, FastAPI as the gateway/orchestrator.
- **LLM:** Google Gemini via `google-genai`, with a rule-based fallback so the
  system degrades gracefully instead of failing when the API is unavailable.
- **NLP:** spaCy for tokenization/keyword/entity extraction feeding both the
  LLM prompt and the fallback path.
- **Information Retrieval:** `sentence-transformers` embeddings + FAISS for
  semantic similarity search, plus the Kaggle API for live results.
- **Security:** JWT-based auth (bcrypt-hashed passwords), input validation via
  Pydantic on every endpoint; prompt-input sanitization against injection is
  planned but not yet implemented (honest gap, see Responsible AI below).
- **Agent communication:** typed Pydantic schemas passed through a FastAPI
  orchestrator today; documented path to splitting agents into independently
  runnable services communicating over HTTP if we want to demonstrate that
  explicitly.
- **Frontend:** Next.js, calling the backend's REST API.
- **Testing plan:** manual endpoint verification now (curl/Swagger UI), unit
  tests for each agent's scoring/classification logic before final submission.
- **Deployment plan:** containerize backend and frontend separately (Docker),
  deploy to a small cloud VM or PaaS (Render/Railway/Fly.io-class service) for
  the final demo; not required for Mid Evaluation.

## 5. Responsible AI plan

- **Transparency:** every NLP Agent response includes `understanding_source`
  (`"llm"` or `"rule_based"`) so it's never ambiguous which path produced a
  result — that's a genuine transparency mechanism, not just a report claim.
- **Explainability:** the Evaluation Agent generates a plain-language reason
  for every ranked result (which domain/task matched, or that it was
  semantically related) instead of a bare score.
- **Fairness:** the rule-based fallback uses fixed keyword lists per domain —
  we're aware this can systematically under-serve phrasings or domains not in
  that list; the LLM path is the primary mitigation, with the fallback kept
  narrow and reviewable rather than trying to be exhaustive.
- **Privacy:** queries are not stored or logged anywhere in the system;
  passwords are bcrypt-hashed and never returned by any endpoint.
- **Security/misuse:** authentication protects account-related endpoints;
  dataset search itself stays open by design (see commercialization below).
  Input sanitization against prompt injection into the LLM step is a known,
  disclosed gap — not yet built, planned as the next security addition.
- **Domain-specific risk:** we can't guarantee the quality or fitness of
  externally-sourced (Kaggle) datasets — the UI tags each result's source
  (`catalog` vs `kaggle`) so users know when a recommendation needs their own
  due diligence before use.

## 6. Commercialization plan

- **Who'd use it:** ML students and researchers (free tier — low willingness
  to pay, high volume), independent practitioners and small research teams who
  search often (paid tier — time saved has direct value to them), and
  labs/companies wanting private dataset integration (enterprise tier).
- **Value proposition:** faster, more precise dataset discovery than manual
  multi-platform search, with transparent reasoning instead of a black box.
- **Pricing/revenue model:** freemium — Free (catalog + basic Kaggle search,
  no cost), Pro (~$19/month — priority LLM access, multi-source discovery,
  unlimited use), Enterprise (custom — private datasets, team seats, API
  access, SLA). Full tier breakdown is live at `/pricing` in the frontend.
- **Deployment/go-to-market:** cloud-hosted SaaS, initial adoption through
  university/research-community channels (where the pain point is sharpest),
  expanding to small ML teams once there's traction.
