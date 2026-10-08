# DATA NEBULA AI — Multi-Agent Dataset Recommendation System

IT3041 (Information Retrieval and Web Analytics) group assignment. A multi-agent AI
system that turns a natural-language dataset request into ranked, explained dataset
recommendations.

## Project overview

The recommendation workflow combines five agent modules:

1. **Query understanding:** the NLP agent identifies the requested domain, task,
   and keywords using Gemini with a rule-based fallback.
2. **Catalog discovery:** the discovery agent uses Sentence-BERT embeddings and
   FAISS to retrieve semantically related datasets from the catalog.
3. **External collection:** the collection agent searches Kaggle, OpenML, and
   Hugging Face on a best-effort basis, supplementing catalog results.
4. **Evaluation:** the evaluation agent ranks candidates using semantic
   similarity, domain alignment, task matching, and keyword relevance, then
   provides explanations for the recommendations.
5. **Personalization:** the recommendation agent uses a signed-in user's search
   history to suggest relevant datasets.

The FastAPI gateway coordinates these modules and returns results to the Next.js
interface. Internal agent communication uses Python functions and Pydantic
models. Ranking scores are heuristic relevance indicators; they are not a
guarantee that a dataset is suitable for a particular research or production use.

## Architecture

```
                    USER
                     |
              Next.js Frontend
                     |
              FastAPI Gateway
                     |
        ---------------------------------
        |                |              |
        v                v              v
   NLP Agent        Discovery Agent   Evaluation Agent
  (Gemini LLM         (FAISS +          (Scoring +
   + spaCy)         Sentence-BERT)      Explanation)
        |                |              |
        ---------------------------------
                    Final Response
        Ranked datasets + relevance score + explanation
```

## Repository structure

```
Multi-Agent-Dataset-AI/
├── backend/
│   ├── agents/
│   │   ├── nlp_agent/               # Query understanding (LLM + rule-based fallback)
│   │   ├── discovery_agent/         # Semantic dataset search (FAISS)
│   │   ├── dataset_collection_agent/ # Live Kaggle/OpenML/HuggingFace search (Kaggle needs an
│   │   │                             #   API token; OpenML/HuggingFace need none — each source
│   │   │                             #   is independently best-effort, never blocks the others)
│   │   ├── evaluation_agent/        # Ranking + explanation
│   │   └── recommendation_agent/    # Personalized recommendations from a signed-in user's search history
│   ├── llm/                   # Gemini API client + prompt templates
│   ├── security/              # Auth, admin panel (users/catalog/plans), input sanitization, encryption (Member 2)
│   ├── responsible_ai/        # Explainability, fairness, privacy (Member 2)
│   ├── main.py                # FastAPI gateway
│   └── requirements.txt
├── frontend/dataset-ai-ui/    # Next.js app (Member 3)
├── database/
├── docs/                      # Assignment brief, source report, member task breakdown
└── README.md
```

See [`docs/members.md`](docs/members.md) for the full per-member task breakdown,
branch layout, and API reference.

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn main:app --reload
```

Add `GEMINI_API_KEY=...` to the **repo-root** `.env` (see `backend/.env.example` for
the full list of variables — it's just a reference, the actual file is read from the
project root). Optional — the NLP Agent falls back to rule-based classification without
it.

`DATA_ENCRYPTION_KEY` is required for stored search-text encryption; retain the persistent key in the repo-root `.env` and back it up securely. See `backend/.env.example`.

Current verification and remaining submission gaps: [full recheck](docs/full-project-recheck.md).

For hosted setup, follow the [two-project Vercel and PostgreSQL guide](docs/vercel-deployment.md). Local deployment preparation is tested; a live Vercel/Neon deployment is not yet verified.

API docs: `http://localhost:8000/docs`

Try the full pipeline:
```bash
curl -X POST "http://localhost:8000/discover?query=I%20need%20datasets%20for%20predicting%20diabetes"
```

### Frontend

```bash
cd frontend/dataset-ai-ui
npm install
npm run dev
```

## Branches

- `main` — stable
- `dev` — integration branch
- `member1-nlp-agent` — NLP / Discovery / Evaluation agents + architecture (Member 1)
- `member2-security-agent` — Security + Responsible AI (Member 2)
- `member3-frontend-ui` — Frontend / UX (Member 3)

## Contributors

- Member 1 — NLP Agent, Discovery Agent, Evaluation Agent, architecture
- Member 2 — Security & Responsible AI
- Member 3 — Frontend & UX
