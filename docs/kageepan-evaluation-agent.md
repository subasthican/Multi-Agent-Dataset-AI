# Evaluation Agent — Kageepan

Location: [`backend/agents/evaluation_agent/`](../backend/agents/evaluation_agent/)

## What this agent is

The Evaluation Agent is the **third and final stage** of the pipeline. The Discovery
Agent already found candidate datasets ranked by raw semantic similarity — but
similarity alone isn't the full picture of relevance. This agent's job is to take those
candidates plus the user's original structured requirement (domain, task, keywords) and
produce a **final relevance score and a human-readable explanation** for each one,
filtering out anything that isn't actually a good match.

In other words: Discovery answers *"what looks similar?"*, Evaluation answers *"how
relevant is this, really, and why?"*.

## Why it's needed

Semantic similarity from embeddings is useful but imperfect — two descriptions can be
textually similar while being about completely different domains or tasks (e.g. a
"vehicle sensor time-series" dataset and a "financial time-series" dataset might score
similarly on pure text similarity despite being irrelevant to each other). This agent
adds structured, rule-based judgment on top of raw similarity so the final ranking
actually reflects domain/task correctness — and it produces the plain-English
explanation ("recommended because it matches the healthcare domain...") that the
frontend shows the user, which is the system's transparency/explainability requirement.

## How it scores and explains (the actual logic)

Each candidate dataset gets a score out of 100, built from four weighted signals
(defined in `scorer.py`):

| Signal | Weight | What it means |
|---|---|---|
| Similarity score (from Discovery Agent) | up to 50 points | `dataset.similarity * 50` |
| Domain match | +25 points | dataset's domain exactly equals the requirement's domain |
| Task match | +15 points | dataset's task exactly equals the requirement's task |
| Keyword hits | +2 points each, capped at 10 | how many of the requirement's keywords appear as whole words in the dataset's description |

That adds up to a maximum of 100. Anything scoring **below 40** is dropped entirely
rather than kept just to pad out the result list — the system would rather show fewer,
genuinely relevant datasets (or an honest "no matches found") than confidently present
something irrelevant as a recommendation.

The keyword-matching step specifically uses **whole-word regex matching**
(`\bkeyword\b`), not a plain substring check. This was an actual bug found and fixed
during development: a plain `"age" in description` check gave a false keyword hit
against the word "usage" — nothing to do with the keyword "age" at all. Word-boundary
matching fixes that while still correctly matching multi-word phrases.

## Files this agent needs, and what each one means

### `agent.py` — the orchestrator
Contains `evaluate_datasets(datasets, requirement)`, the function the rest of the system
calls. For every candidate dataset it:
1. Calls `calculate_score()` (from `scorer.py`) to get the final numeric score.
2. Calls `generate_explanation()` to build the human-readable reason string.
3. Wraps both into an `EvaluatedDataset`.

It then sorts everything by score (highest first) and filters out anything below
`MIN_RELEVANCE_SCORE` (40.0) before returning the final list. `generate_explanation()`
is also defined here: it checks whether the domain matched, whether the task matched,
and builds a sentence like *"X is recommended because it matches the healthcare domain
and matches the classification task, with a relevance score of 82.0%."* — falling back
to *"is semantically related to the request"* if neither matched but it still cleared
the relevance floor on similarity/keywords alone.

### `scorer.py` — the actual scoring formula
This is where the weighted scoring logic described in the table above lives:
- `calculate_score(dataset, requirement)` — combines similarity, domain match, task
  match, and keyword hits into the final 0–100 score, capped at 100.
- `_contains_keyword(description, keyword)` — the whole-word regex match helper used for
  the keyword-hit signal, specifically written to avoid the substring false-positive bug
  described above.
- The weight constants (`SIMILARITY_WEIGHT`, `DOMAIN_MATCH_WEIGHT`, `TASK_MATCH_WEIGHT`,
  `KEYWORD_MATCH_WEIGHT_PER_HIT`, `KEYWORD_MATCH_MAX`) are defined at the top of this
  file as named constants rather than "magic numbers" buried in the formula, so the
  scoring weights can be understood and tuned in one place.

### `models.py` — the data contract
Defines `EvaluatedDataset` — the final output shape for one dataset: the original
`dataset` (a `DatasetMatch` from the Discovery Agent), its computed `score`, and its
`explanation` string. This is what actually gets sent back to the frontend as the
final search result.

### Files outside this folder that this agent depends on
This agent doesn't own any data of its own — it purely evaluates what the other two
agents produced, so it directly reuses their schemas instead of redefining them:
- [`backend/agents/discovery_agent/models.py`](../backend/agents/discovery_agent/models.py)
  — for `DatasetMatch`, the shape of each candidate dataset being scored.
- [`backend/agents/nlp_agent/models.py`](../backend/agents/nlp_agent/models.py) — for
  `QueryAnalysisResult`, the shape of the original requirement being matched against.

## Summary of the flow

```
DiscoveryResult (list of DatasetMatch, from Discovery Agent)
   +  QueryAnalysisResult (from NLP Agent)
   →  calculate_score() per dataset (scorer.py: similarity + domain + task + keywords)
   →  generate_explanation() per dataset (agent.py)
   →  sort by score, drop anything below the 40.0 relevance floor
   →  List[EvaluatedDataset]  →  returned to the user as the final ranked results
```
