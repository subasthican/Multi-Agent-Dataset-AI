# Mid Evaluation Prep — Member 3 (Evaluation Agent + Frontend)

For the Week 6/7 Mid Evaluation: a 15-minute discussion, no slides, 20 marks. The
lecturer is checking **understanding of the plan**, not how much is built. You are
not expected to have a working system yet, but you must be able to explain and
justify every decision below — including the parts you didn't personally write.

> Read this whole file even though it's "your" file — the brief is explicit that
> **every member must be ready to answer all 6 questions**, not just their own
> section. [`member1-nlp-agent.md`](member1-nlp-agent.md) and
> [`member2-security-agent.md`](member2-security-agent.md) have the same 6
> answers with a different "your files" section — read those too before the
> evaluation.

## Your files

| Path | What it is |
|---|---|
| `backend/agents/evaluation_agent/agent.py` | `evaluate_datasets(datasets, requirement)` — scores, ranks, explains |
| `backend/agents/evaluation_agent/scorer.py` | The scoring formula: similarity + domain match + task match + keyword overlap |
| `backend/agents/evaluation_agent/models.py` | `EvaluatedDataset` schema |
| `frontend/dataset-ai-ui/app/page.tsx` | The main search page — wires the search box, agent-flow visualization, and results together |
| `frontend/dataset-ai-ui/components/SearchBox.tsx`, `AgentFlow.tsx`, `DatasetCard.tsx`, `ExplanationCard.tsx`, `LoadingAnimation.tsx`, `GalaxyBackground.tsx`, `Navbar.tsx` | All UI components |
| `frontend/dataset-ai-ui/app/login`, `register`, `forgot-password`, `reset-password`, `profile`, `pricing` | All account + commercialization pages |
| `frontend/dataset-ai-ui/contexts/AuthContext.tsx`, `components/AuthCard.tsx` | Auth state management + shared auth form UI |
| `frontend/dataset-ai-ui/services/api.ts` | The typed client that calls every backend endpoint |

You own the entire user-facing layer *and* the agent that decides what gets
shown and why — the natural pairing, since your `ExplanationCard` component is
literally displaying the Evaluation Agent's explanation strings.

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

1. **NLP Agent** (Member 1) — converts the raw query into structured intent
   using an LLM with a rule-based fallback. *Necessary because* nothing
   downstream can search meaningfully without first turning free text into
   structured fields.

2. **Discovery Agent** (Member 2) — takes the structured intent and finds
   candidate datasets via semantic search (embeddings + FAISS) over a curated
   catalog, plus live Kaggle search results. *Necessary because* this is the
   actual retrieval step.

3. **Evaluation Agent** (mine) — takes the candidate datasets and computes a
   relevance score for each: a weighted combination of semantic similarity,
   domain match, task match, and keyword overlap with the user's request —
   then sorts by score and generates a plain-language explanation for every
   result (e.g. *"matches the healthcare domain and the classification task"*).
   *Necessary because* a raw similarity-ranked list isn't enough — a user
   needs to know *why* something was recommended before they trust it, which
   is also the piece of the system my frontend work displays directly.

**Communication:** the three agents are chained through the FastAPI
orchestrator (`POST /discover`) using typed Pydantic schemas — my Evaluation
Agent receives the Discovery Agent's `DatasetMatch` list plus the NLP Agent's
`QueryAnalysisResult`, and returns a sorted list of `EvaluatedDataset` objects
that the frontend renders directly as result cards. Currently in-process
function calls; could become an independently deployed HTTP service without
changing that interface if we want to demonstrate literal inter-process
communication.

**Collectively:** query in, structured understanding, semantic retrieval,
ranked and explained results out — three narrow specialists producing one
coherent answer none of them could produce alone, which my frontend then
presents as a live, animated pipeline (`AgentFlow.tsx`) so the user can see
which agent is working at each stage.

## 4. Implementation plan

- **Backend:** Python, FastAPI as the gateway/orchestrator.
- **LLM:** Google Gemini via `google-genai`, with a rule-based fallback.
- **NLP:** spaCy for tokenization/keyword/entity extraction.
- **Information Retrieval:** `sentence-transformers` embeddings + FAISS,
  plus live Kaggle search.
- **Evaluation (mine):** a scoring formula combining FAISS/cosine similarity
  with domain, task, and keyword match bonuses (implemented as named
  constants, not magic numbers, so the weighting is easy to tune and
  explain), sorted descending, each with a generated explanation string.
- **Security:** JWT-based auth, bcrypt password hashing; input sanitization
  against prompt injection is planned but not yet implemented.
- **Frontend (mine):** Next.js (App Router), Tailwind for styling,
  Framer Motion for animation, `@react-three/fiber`/`drei` for the animated
  starfield background. A typed `services/api.ts` client calls every backend
  endpoint — no hardcoded response shapes, matching the backend's Pydantic
  schemas.
- **Agent communication:** typed Pydantic schemas through a FastAPI
  orchestrator today; documented path to HTTP-based inter-service
  communication if needed.
- **Testing plan:** manual endpoint + UI verification now; before final
  submission, tests for the scoring formula's behavior on edge cases
  (no domain/task match at all, tied scores) and for the frontend's handling
  of empty results / backend errors.
- **Deployment plan:** containerize backend and frontend (Docker), deploy to
  a small cloud host for the final demo; not required for Mid Evaluation.

## 5. Responsible AI plan

- **Transparency/Explainability (mine):** every recommendation shown in the
  UI carries its match score *and* a plain-language reason — never a bare
  ranked list. The `ExplanationCard` component also surfaces whether the NLP
  understanding came from the LLM or the rule-based fallback, so the
  transparency isn't just in the backend response, it's visible to the user.
- **Fairness:** the scoring weights (similarity vs. domain/task/keyword
  match) are fixed constants applied identically to every query — no
  per-user or per-query special-casing that could introduce inconsistent
  treatment.
- **Privacy:** no queries are logged or stored; the frontend doesn't persist
  search history anywhere (the "saved history" pricing feature is explicitly
  marked "coming soon," not implemented, to avoid overclaiming).
- **Security:** the frontend never handles raw passwords beyond submitting
  them over HTTPS-capable fetch calls to the backend's auth endpoints; the
  JWT is stored in `localStorage` — a reasonable tradeoff for this project's
  scope, though worth noting in viva that an httpOnly cookie would be more
  robust against XSS in a production system.
- **Misuse/domain risk:** the UI tags each result's source (catalog vs.
  Kaggle) so users can judge how much to trust an unreviewed live result
  versus a curated one — a UI-level transparency measure supporting the
  same mitigation Member 2's Discovery Agent relies on.

## 6. Commercialization plan

- **Who'd use it:** ML students and researchers (free tier — low willingness
  to pay, high volume), independent practitioners and small research teams
  who search often (paid tier — time saved has direct value), and
  labs/companies wanting private dataset integration (enterprise tier).
- **Value proposition:** faster, more precise dataset discovery than manual
  multi-platform search, with transparent reasoning instead of a black box.
- **Pricing/revenue model (mine to present, built at `/pricing`):** freemium
  — Free (catalog + basic Kaggle search), Pro (~$19/month — priority LLM
  access, multi-source discovery, unlimited use), Enterprise (custom —
  private datasets, team seats, API access, SLA). Be upfront if asked: the
  pricing page is the commercialization *plan*, not working billing — no
  payment provider is wired in yet.
- **Deployment/go-to-market:** cloud-hosted SaaS, initial adoption through
  university/research-community channels, expanding to small ML teams once
  there's traction.
