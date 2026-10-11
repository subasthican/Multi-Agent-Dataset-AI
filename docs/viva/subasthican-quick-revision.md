# Subasthican's quick revision sheet

Read the [full guide](subasthican-study-guide.md) for context. Prepared 8 October 2026 from code at `b520e20`; results refer to saved 5 October evidence.

## Your 30-second introduction

“DATA NEBULA AI recommends datasets from a plain-English request. My main responsibility is the NLP agent and orchestration. I validate and preprocess the request, extract structured intent with Gemini or local rules, and pass that understanding to retrieval and evaluation. My proposed individual assessment examines prompt injection and malformed model responses. I explain the baseline failures, the later defenses, and the limits of the evidence.”

## The project in one line

User request → NLP understanding → catalog/external retrieval → eligibility checks and score → explained dataset links.

## The eight facts you should remember

1. **Your group part:** NLP and orchestration. Proposed individual part: prompt injection/jailbreak assessment.
2. **Your main function:** `analyze_query()` in `backend/agents/nlp_agent/agent.py`.
3. **Your output:** domain, task, data type, keywords, entities, source label, warnings and clarification flag.
4. **Local NLP:** spaCy tokens, noun/proper-noun lemmas, stopword filtering and NER.
5. **Understanding:** validated Gemini JSON first, deterministic rules when unavailable/unusable.
6. **Two trust boundaries:** user input and model output.
7. **Best case:** PI-V10 supplied numeric keywords. Baseline TypeError; saved fixed retest rejects and falls back.
8. **Evidence limit:** guard/fixture passes do not prove live Gemini attack resistance.

## Numbers, with their meanings

| Number | Meaning |
|---|---|
| 300 | Maximum query characters |
| 20 | Maximum model keywords; also maximum API result count `k`, a separate limit |
| 60 | Maximum characters per model keyword |
| 10 | Current seed catalog entries, all tabular |
| 40 | Evaluation's minimum relevance score |
| 50 / 25 / 15 / 10 | Maximum scoring contributions: similarity / domain / task / keyword overlap |
| 15 blocked | Original live input assessment cases, with failed provider access |
| 13 fail + 2 pass | Original controlled output fixtures |
| 15 + 15 pass | Saved input-guard retests and controlled output retests, different evidence scopes |

## Statements to correct if an examiner challenges you

| Overstatement | Accurate answer |
|---|---|
| “Every test proved Gemini resisted attacks” | Input guards and controlled fixtures passed; full live resistance remains unverified |
| “The whole app is 100% secure” | Finite tests support specific behavior, with documented limits |
| “All agents use Gemini” | The NLP agent calls Gemini; the others mainly use algorithms/rules |
| “The agents use MCP” | They use Python calls and Pydantic objects; Neon MCP is development tooling |
| “FAISS uses L2 in this project” | Current code uses normalized vectors and `IndexFlatIP` |
| “86% is model accuracy” | It is a heuristic relevance score |
| “We encrypt everything” | Fernet protects stored query text; other fields have different protection |
| “Kidney understanding means kidney data is available” | Interpretation and candidate availability are separate |

## Last practice before the viva

- Explain diabetes classification versus house-price regression.
- Open `agent.py` and identify input checks, spaCy, Gemini, schema validation and fallback.
- Open [PI-V10 baseline](../individual-assessments/evidence/PI-V10.json) and [retest](../fix-verification/evidence/PI-V10.json).
- Explain what each result proves in your own words.
- Rehearse the [12-slide script](subasthican-presentation.md), then answer questions without reading it.
- State which work and tests you personally performed. Do not claim authorship or independent execution you cannot defend.
