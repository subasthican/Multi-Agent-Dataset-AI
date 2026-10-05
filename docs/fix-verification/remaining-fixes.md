# Remaining application fixes — 5 October 2026

Duplicate handling is fixed and the expanded catalog ranking checks pass. Gemini error handling is improved, but live Gemini evaluation remains blocked by the provider. SMTP and group/individual submissions are excluded at the user's request.

| Check after fixes | Result |
|---|---|
| Existing isolated application suite | 69 PASS, 0 FAIL, 0 ERROR |
| New dataset identity, collection and Gemini cooldown unit tests | 23 PASS |
| Catalog NLP/ranking validation | 38 PASS: 30 positive requests, 8 abstention requests |
| Original four ranking smoke queries | 4 PASS |
| Original duplicate case | PASS: 1 card instead of 2 |
| HTTP duplicate/distinct identity and abstention checks | 3 PASS |
| Backend compilation / installed dependencies | PASS |
| Latest authenticated Kaggle search | PASS: 3 datasets |
| Latest configured Gemini model | BLOCKED: one remote request returned daily-quota exhaustion |
| New Gemini attack requests | 0 attempted; 15 cases explicitly skipped after quota failure |

## Duplicate handling

The collection agent and full coordinator now reconcile `(source, id)` and equivalent reference URLs. Known Kaggle/OpenML/Hugging Face references normalize their www host, HTTP redirect, default port, trailing slash, tracking parameters and dataset-page anchors. Catalog metadata takes priority because catalog candidates are supplied first. A source ID can also bridge a catalog URL and a previously URL-less source result.

Different dataset URLs, version qualifiers, functional query parameters, unknown-site hash routes, path case and nonstandard ports are kept distinct unless an explicit shared source ID establishes identity. Similar names alone do not trigger a merge. Copies on separate platforms with different URLs still need trustworthy provenance linking them; the app does not guess that relationship.

The HTTP check used real coordinator/NLP/embedding/evaluation code with declared external-result and unavailable-provider fixtures in a disposable database. It verified one catalog copy of the duplicate and retention of a separate dataset. No live duplicate prevalence measurement is claimed.

## Ranking and English fallback

Added fixed query judgments covering every one of the ten seeded datasets, with three requests per dataset and eight requests that should produce no compatible catalog results. Validation exposed short English technical requests being rejected by language detection, missing inflected task verbs, and incomplete housing/property vocabulary. Those fallback rules are corrected. The recorded pre-fix validation has 35 passes and 3 failures; the final run has 38 passes.

Positive top-1 accuracy, MRR@3, recall@3 and single-target NDCG@3 are 1.0 for these 30 authored queries; the eight catalog abstention cases also pass. These are finite project-authored validation results, not independently annotated general accuracy. Single-target judgments do not measure every returned card's relevance, external search quality, score calibration or population fairness. Ranking weights remain heuristic.

## Gemini handling and external blocker

The SDK now makes one attempt with a 30-second timeout. Structured daily quota, short-window rate-limit and service-unavailable responses start a cooldown scoped to the model and credential. Repeated requests during that cooldown use the existing rule-based fallback without another provider request. The next request after the delay can probe the provider again. Changing the credential selects a new SDK client.

Cooldown state is in memory in each backend process; restarts and other workers do not share it. It cannot replenish Google's quota. Where the provider supplies no daily reset delay, the app permits another probe after one hour without claiming the quota has reset.

The configured `gemini-3.5-flash` returned `429` with daily allowance 20 and retry delay 24,328 seconds at the latest observation (about 6 hours 45 minutes). A diagnostic `gemini-3.8-flash` attempt returned `503` high demand. The configured model and credentials were not changed, and no billing change was made. The two remaining normal queries and all 15 attack requests were skipped after the latest daily error; skipped cases are not safety passes. The live runner now records actual provider attempts separately from blocked case labels.

After quota resets, rerun `python docs/fix-verification/run_live_integrations.py` using the installed backend environment. Full live model verification remains pending until the provider can return usable responses.

## Browser and preservation

Frontend source was unchanged, so earlier lint/type/build passes and 12 manually verified Chrome flows are retained as earlier evidence. An additional attempt to view the duplicate fixture could not proceed because native browser control repeatedly reported user activity; no new browser pass is claimed. The corresponding HTTP behavior passed. Full cross-browser/mobile and selected password/deletion UI flows remain outside the existing manual coverage.

The temporary API/frontend servers were stopped. Tests kept the working database unchanged, and original individual assessment evidence remains preserved. A reproducible disposable browser fixture is supplied in `serve_browser_fixture.py`; its source results and provider fallback are explicitly mocked.

## Evidence and reproduction

- [Combined current results and source hashes](evidence/remaining-fixes.json)
- [Application case results](evidence/results.json)
- [23 unit-test output](evidence/remaining-fixes-unit-tests.txt)
- [38 ranking outcomes and metrics](evidence/ranking-validation.json), [pre-fix outcomes](evidence/ranking-validation-before.json), [fixed query judgments](ranking-cases.json)
- [Duplicate and original ranking smoke results](evidence/supplemental-validation.json)
- [HTTP pipeline checks](evidence/remaining-fixes-http.json)
- [Latest live provider summary](evidence/live-integrations/summary.json)

Run from the repository root with the backend dependencies and models installed:

```sh
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
python docs/fix-verification/run_retests.py
python docs/fix-verification/run_supplemental_validation.py
python docs/fix-verification/run_ranking_validation.py
```

The first, supplemental and ranking commands return a nonzero exit status on failure. The existing application harness also records each outcome in its evidence. No 100% project or security completion claim is made.
