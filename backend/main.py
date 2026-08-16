from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from agents.nlp_agent.agent import analyze_query
from agents.nlp_agent.models import QueryAnalysisResult

app = FastAPI(title="Dataset AI Agent System")


@app.get("/")
def home():
    return {"message": "Multi Agent Dataset Recommendation System"}


@app.post("/nlp-agent", response_model=QueryAnalysisResult)
def nlp_agent(query: str):
    try:
        return analyze_query(query)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc
