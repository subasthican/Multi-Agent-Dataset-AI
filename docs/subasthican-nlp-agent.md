# NLP Agent — Subasthican

Location: [`backend/agents/nlp_agent/`](../backend/agents/nlp_agent/)

## What this agent is

The NLP Agent is the **first stage** of the pipeline. A user types a plain-English
request like *"I need a medical dataset to predict diabetes"* — this agent's whole job
is to turn that unstructured sentence into a structured object the rest of the system
can actually work with:

```json
{
  "domain": "healthcare",
  "task": "classification",
  "data_type": "tabular",
  "keywords": ["medical", "dataset", "diabetes"],
  "entities": [],
  "understanding_source": "llm"
}
```

Nothing downstream (Discovery Agent, Evaluation Agent) understands free text — they only
understand `domain`, `task`, and `keywords`. This agent is the translator between "what a
human typed" and "what the system can search and score with."

## Why it's needed

Without this agent, the system would have to make the user fill in a rigid form
("domain: ___", "task: ___") instead of just describing what they want in their own
words. That's the actual Information Retrieval / NLP requirement of the assignment: the
system has to *understand* a query, not just accept pre-categorized input.

## How it understands a query (two layers)

1. **LLM understanding (primary)** — the cleaned query is sent to Google's Gemini model
   with a fixed instruction prompt asking for `domain`, `task`, `keywords`, and
   `data_type` back as JSON. This gives much better real-world understanding (it can
   infer "cancer" → `healthcare` even if "cancer" isn't in any hardcoded list).
2. **Rule-based fallback (secondary)** — if there's no Gemini API key configured, or the
   LLM call fails, or it returns something that isn't valid/usable JSON, the agent falls
   back to a deterministic keyword-matching classifier. This means the agent **never
   fails outright** — it always returns a usable result, just with a label
   (`understanding_source: "llm"` or `"rule_based"`) saying which method produced it.

Either way, actual NLP preprocessing (tokenizing, lemmatizing, stopword removal, part-of-
speech tagging, named-entity recognition) always runs first via spaCy — the LLM/rule
split only decides how `domain`/`task`/`data_type` get classified, not whether the text
gets processed at all.

## Files this agent needs, and what each one means

### `agent.py` — the orchestrator
This is the entry point: `analyze_query(text)`. It ties every other file together in
order:
1. Validates input with `QueryInput` (from `models.py`).
2. Cleans the text and runs it through spaCy (`preprocessing.py`) to get keywords and
   entities.
3. Tries the LLM path first (`_understand_with_llm`, using `backend/llm/prompts.py` and
   `backend/llm/gemini_client.py`).
4. If the LLM path doesn't return something usable, falls back to the rule-based
   classifiers (`classify_domain`, `classify_task`, `classify_data_type`), which read
   their keyword lists from `config.json`.
5. Returns a `QueryAnalysisResult`.

It also contains `_match_category` — the actual rule-based matching logic. It does
**whole-word matching** with regex word boundaries (`\btrigger\b`), not a plain substring
check. This matters: a naive `"car" in text` check would wrongly match inside words like
"scarcity" or "healthcare". This was an actual bug caught and fixed during development.

### `preprocessing.py` — the raw NLP work
This is where actual NLP techniques from the syllabus are applied, using spaCy
(`en_core_web_sm` model):
- `clean_text()` — collapses whitespace/trims the raw string.
- `extract_keywords()` — runs the spaCy pipeline (tokenization → POS tagging →
  lemmatization) and keeps only nouns/proper nouns, skipping stopwords and punctuation.
  This is what turns "I need datasets about diseases" into `["dataset", "disease"]`.
- `extract_entities()` — runs spaCy's Named Entity Recognition and returns anything it
  finds (e.g. organizations, locations) as `{"text": ..., "label": ...}` pairs.
- `get_nlp_model()` — loads the spaCy model once and caches it (`lru_cache`), since
  loading a language model is expensive and should not happen on every request.

### `config.json` — the rule-based agent's "knowledge"
A plain JSON file of keyword lists, grouped under three keys: `domains`, `tasks`,
`data_types`. Example: under `domains.healthcare` there's `["health", "medical",
"disease", "patient", "diagnosis", "clinical", "cancer", "diabetes", "hospital",
"drug"]`. This file *is* the rule-based classifier's logic — no keyword lists are
hardcoded inside `agent.py` itself, so adding a new domain/task/data-type category is a
one-line JSON edit, not a code change. This file is only consulted when the LLM path
isn't available.

### `models.py` — the data contracts
Defines the exact shape of data going in and out, using Pydantic:
- `QueryInput` — validates the raw request (must be 1–300 characters, gets stripped of
  whitespace, rejects empty/whitespace-only input).
- `QueryAnalysisResult` — the structured output described above: `original_query`,
  `domain`, `task`, `data_type`, `keywords`, `entities`, and `understanding_source`.

Having this as a strict schema (instead of a loose dict) is what lets the Discovery and
Evaluation agents trust the shape of what this agent hands them — a field can't
mysteriously go missing or be the wrong type without Pydantic raising an error
immediately, at the source.

### Files outside this folder that this agent depends on
- [`backend/llm/gemini_client.py`](../backend/llm/gemini_client.py) — wraps the actual
  call to Google's Gemini API (`generate_response()`), and raises
  `LLMUnavailableError` if there's no API key or the call fails, which is what
  `agent.py` catches to trigger the rule-based fallback.
- [`backend/llm/prompts.py`](../backend/llm/prompts.py) — holds `dataset_prompt()`, the
  exact instruction text sent to Gemini asking it to return `domain`/`task`/`keywords`/
  `data_type` as JSON.

## Summary of the flow

```
raw text  →  QueryInput (validate)  →  spaCy (clean, keywords, entities)
          →  try Gemini LLM (prompts.py + gemini_client.py)
          →  if that fails/unusable: rule-based classify (config.json)
          →  QueryAnalysisResult  →  passed to the Discovery Agent
```
