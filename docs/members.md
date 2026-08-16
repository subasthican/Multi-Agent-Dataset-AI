# Team & Module Breakdown — DATA NEBULA AI

Source: `Group Assignment Brief.pdf` (IT3041 – Information Retrieval and Web Analytics)
and `IRWA CHATGPT FULL REPORT.docx`.

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
      ├── member1-nlp-agent        (created)
      ├── member2-security-agent   (scaffolded — see note below)
      └── member3-frontend-ui      (scaffolded — see note below)
```

> **Open question to confirm with your group:** the source report contains two
> slightly different role splits from different planning sessions:
> - *Split A (original architecture diagram):* Member 2 = IR/Discovery Agent (vector
>   search, FAISS), Member 3 = Evaluation Agent (ranking/explanation).
> - *Split B (later, more detailed section):* Member 2 = Security + Responsible AI,
>   Member 3 = Frontend/UX.
>
> The scaffolding below follows **Split B** since it's the more fully worked-out plan
> in the report, which leaves the IR/Discovery and Evaluation agents as part of Member
> 1's backend/agents work. Confirm this with Gowsika and Kageepan before they start —
> if you actually want Split A, the folder names just need swapping and the IR module
> requirement moves to Member 2's branch instead.

## Member 1 — NLP Agent + Architecture Lead (this repo, `member1-nlp-agent`)

**Status: implemented.**

- `backend/agents/nlp_agent/`
  - `agent.py` — orchestrates a query: validate → clean → spaCy pipeline → classify.
  - `preprocessing.py` — spaCy model loading, keyword/entity extraction.
  - `models.py` — Pydantic request/response schemas (`QueryInput`, `QueryAnalysisResult`).
  - `config.json` — domain/task/data-type trigger keywords. Editable without touching code.
- `backend/main.py` — FastAPI gateway, exposes `POST /nlp-agent`.
- `backend/requirements.txt` — fastapi, uvicorn, spacy, pydantic.

Run it:
```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn main:app --reload
```
Test at `http://localhost:8000/docs`, `POST /nlp-agent?query=Find healthcare datasets for cancer prediction`.

Still open for Member 1: Discovery/IR Agent (semantic search over a dataset index,
e.g. FAISS + embeddings) and Evaluation Agent (ranking + explanation), per Split B above.

## Member 2 — Security Agent + Responsible AI (`member2-security-agent`, scaffolded)

Folder structure to fill in:
```
backend/security/
  authentication.py   # JWT issuing/verification
  jwt_manager.py
  input_filter.py      # prompt-injection / malicious input filtering
  encryption.py         # Fernet-based field encryption
backend/responsible_ai/
  fairness.py            # bias/fairness check on ranked results
  explainability.py    # human-readable reasoning for a recommendation
  privacy.py               # strip sensitive fields before storage/logging
```
Tasks:
1. JWT authentication protecting the FastAPI endpoints.
2. Input sanitization layer (block prompt-injection patterns) applied before queries reach the LLM/agents.
3. Encryption helpers for any stored user data.
4. Responsible AI layer: explanation generator, fairness check, privacy scrubber.
5. Wire sanitization + auth into the shared API (coordinate with Member 1 on `main.py`).
6. `docs/security.md` write-up for the report.

## Member 3 — Frontend + UX (`member3-frontend-ui`, scaffolded)

Folder structure to fill in (inside `frontend/dataset-ai-ui`):
```
app/dashboard/page.tsx
components/Navbar.tsx
components/SearchBox.tsx
components/DatasetCard.tsx
components/AgentFlow.tsx
components/LoadingAnimation.tsx
components/ExplanationCard.tsx
services/api.ts
```
Tasks:
1. Space-themed UI (dark gradient background, glassmorphism cards, framer-motion animations).
2. Search box that calls `POST /nlp-agent` (and later the IR/Evaluation endpoints) via `services/api.ts`.
3. Dataset result cards + an "agent activity" visualization (NLP → IR → Evaluation flow).
4. Responsive layout, loading states, error states.
5. Connect to Member 2's auth flow once available.

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
