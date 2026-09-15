# Discovery Agent — Gowsika

Location: [`backend/agents/discovery_agent/`](../backend/agents/discovery_agent/)

## What this agent is

The Discovery Agent is the **second stage** of the pipeline — the actual Information
Retrieval (IR) component the assignment requires. It takes the structured understanding
the NLP Agent produced (domain, task, keywords) and uses it to **find candidate
datasets** from a curated local catalog, returning them ranked by semantic similarity to
the original query.

This is not keyword/SQL matching — it's real IR using vector embeddings and cosine
similarity, i.e. it understands that a query about "predicting patient risk" and a
dataset described as "clinical records for disease diagnosis" are related even though
they don't share exact words.

## Why it's needed

The NLP Agent only understands what the user *wants*; it has no idea what datasets
actually *exist*. The Discovery Agent is the bridge between "what the user is asking
for" and "what's actually in the catalog" — it's the search/retrieval engine of the
system, and it's what makes this an Information Retrieval project rather than just an
NLP one.

## How it retrieves datasets (the IR technique used)

1. Every dataset in the catalog has its `description` turned into a numeric vector
   (an embedding) using a sentence-transformer model (`all-MiniLM-L6-v2`).
2. These vectors are loaded into a FAISS index (`IndexFlatL2`) — a library built
   specifically for fast similarity search over vectors, from Facebook AI Research.
3. The user's query is embedded the same way, and FAISS returns the `k` closest
   datasets by distance in that vector space.
4. That raw distance is converted to a 0–1 similarity score
   (`similarity = 1 / (1 + distance)`) so a higher number always means "more similar,"
   which is what the Evaluation Agent expects.

This whole approach means dataset matching is based on **meaning**, not exact keyword
overlap — which is the actual point of using embeddings instead of a plain text search.

## Files this agent needs, and what each one means

### `agent.py` — the entry point
A small, deliberately thin file. `search_datasets(query, k)` is the one function the
rest of the system calls: it runs the vector search (`vector_store.py`) and wraps the
raw dict results into validated `DatasetMatch` objects (`models.py`), returning a
`DiscoveryResult`. Kept thin on purpose — all the actual retrieval logic lives in
`vector_store.py` so this file's only job is "call the search, validate the shape."

### `vector_store.py` — the actual retrieval engine
This is where the IR technique described above is implemented:
- `load_datasets()` — pulls every row from the `catalog_datasets` table in the database
  (not a static file — this catalog is admin-editable) and caches it in memory, since
  hitting the database on every single search would be wasteful.
- `build_index()` — turns every dataset's description into an embedding (via
  `embeddings.py`) and builds the FAISS index from them, also cached.
- `invalidate_cache()` — clears both caches. This gets called whenever an admin
  adds/edits/deletes a catalog entry, so a change to the catalog shows up in search
  results immediately instead of only after a server restart.
- `search_vectors(query, k)` — embeds the query, asks FAISS for the `k` nearest
  datasets, and returns them with a computed similarity score attached.

### `embeddings.py` — turning text into vectors
Wraps the `sentence-transformers` library:
- `get_embedding_model()` — loads the `all-MiniLM-L6-v2` model once and caches it
  (loading a transformer model on every request would be far too slow).
- `create_embeddings(texts)` — turns a list of strings into a list of numeric vectors.
- `rank_by_similarity(query, texts)` — computes cosine similarity between the query and
  a list of texts, used specifically by the external dataset sources (Kaggle, OpenML,
  HuggingFace collection agent) so every source — local catalog or external API — scores
  matches on the same comparable 0–1 scale.

### `models.py` — the data contracts
Pydantic schemas defining every shape this agent deals with:
- `DatasetMatch` — one retrieved dataset: `id`, `name`, `domain`, `task`, `description`,
  `similarity`, `source` (which platform it came from — `catalog`, `kaggle`, `openml`,
  or `huggingface`), and an optional `url` (a real clickable link to the dataset's page,
  left `null` rather than ever being invented for a catalog entry that has no real page).
- `DiscoveryResult` — the full response: the original `query` plus its list of
  `matches`.
- `CatalogDatasetCreate` / `CatalogDatasetUpdate` / `CatalogDatasetResponse` — the
  schemas used by the admin panel to add, edit, and list catalog entries (`name`,
  `description`, `domain`, `task`, optional `url`).

### `seed.py` — first-run catalog setup
`seed_catalog_if_empty()` runs once at server startup. It checks whether the
`catalog_datasets` database table already has any rows; if it's completely empty (i.e.
this is the very first run, or every seed entry was deliberately deleted), it loads
`datasets.json` and inserts those as the starting catalog. If the table already has data
— including an admin having removed some seed entries on purpose — this does nothing, so
it can never silently undo an admin's changes.

### `datasets.json` — the starting catalog data
A plain JSON array of the 10 original curated dataset entries (name, description,
domain, task) used only to seed the database the very first time the app runs. After
that first run, the database — not this file — is the real source of truth; the admin
panel edits the database directly, and this file is never read again unless the catalog
table is completely emptied.

## Summary of the flow

```
QueryAnalysisResult (from NLP Agent)
   →  embed the query (embeddings.py)
   →  FAISS similarity search over embedded catalog descriptions (vector_store.py)
   →  DatasetMatch objects with a similarity score (agent.py, models.py)
   →  DiscoveryResult  →  passed to the Evaluation Agent
```
