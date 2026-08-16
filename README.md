# DATA NEBULA AI — Multi-Agent Dataset Recommendation System

IT3041 (Information Retrieval and Web Analytics) group assignment. A multi-agent AI
system that turns a natural-language dataset request into ranked, explained dataset
recommendations.

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
│   │   ├── dataset_collection_agent/ # Live Kaggle search (optional)
│   │   └── evaluation_agent/        # Ranking + explanation
│   ├── llm/                   # Gemini API client + prompt templates
│   ├── security/              # Auth, input sanitization, encryption (Member 2)
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
