from fastapi import FastAPI
from agents.nlp_agent.agent import analyze_query


app = FastAPI(
    title="Dataset AI Agent System"
)


@app.get("/")
def home():
    return {
        "message":
        "Multi Agent Dataset Recommendation System"
    }


@app.post("/nlp-agent")
def nlp_agent(query:str):

    result = analyze_query(query)

    return result
