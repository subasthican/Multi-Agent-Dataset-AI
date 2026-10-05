**Superseded implementation status:** duplicate reconciliation is now fixed and 38 catalog ranking/abstention cases pass. See [current remaining-fixes report](remaining-fixes.md). The observations below describe earlier runs; their duplicate failure is historical. Gemini live evaluation remains provider-blocked.

# Earlier complete test attempts — 5 October 2026

The application regression suite and selected browser flows passed. A separate duplicate-identity check failed, and live Gemini evaluation remained blocked by the daily quota. This is not a 100% completion claim.

| Area | Outcome |
|---|---|
| Application regression suite | 69 PASS, 0 FAIL, 0 ERROR |
| Frontend lint / TypeScript / production build | PASS |
| Installed backend dependencies | PASS |
| Encrypted database / repeat migration / authorized readback | PASS; all 4 users, 10 catalog rows and 26 history rows retained; working database unchanged during tests |
| Native Chrome checks | 12 PASS; synthetic isolated database |
| Authenticated Kaggle | PASS; direct query returned 3 datasets; browser search also showed live Kaggle cards |
| Live normal Gemini queries | 1 PASS, 0 FAIL, 2 BLOCKED |
| Live Gemini attack cases | 0 PASS, 0 FAIL, 15 BLOCKED by 429 daily-quota errors |
| Supplemental seed-ranking checks | 4 PASS |
| Supplemental cross-source duplication check | FAIL: identical URL/dataset returned 2 cards; expected 1 |

## Exact Gemini limitation

Google reported `GenerateRequestsPerDayPerProjectPerModel-FreeTier` exhausted for `gemini-3.5-flash`, with daily limit **20**. The captured response requested a retry after approximately 7 hours 50 minutes. The key is accepted; the daily allowance is exhausted. Increasing spacing between requests cannot resolve this daily limit. Retry after quota reset or use a provider/model with available quota. No paid change or model configuration change was made.

## Browser scope

Verified homepage, synthetic admin sign-in/profile, admin list/self-protection controls, catalog edit/save, resulting audit entry, plans, pricing, keyboard and pointer searches through the full local pipeline, sign-out, ordinary-user admin redirect and audit denial. Search results showed declared rule-based fallback and live Kaggle records. Both users were signed out, browser password prompts declined, the test tab closed and temporary test servers stopped.

These were manual native Chrome interactions with returned accessibility state and a screenshot inspection, not an automated cross-browser suite. No stored screenshot artifact is claimed. Password-change/reset-delivery/deletion submissions, all responsive device sizes and every UI edge case remain outside these browser checks. The dev logs contain a non-blocking THREE.Clock deprecation warning.

## Ranking and duplicate scope

Four project-authored seed examples returned their expected top result (diabetes, student dropout, stock forecasting and solar forecasting). This is a smoke check, not independent relevance benchmarking or a measured broad accuracy rate. The controlled duplicate case used identical canonical source URLs and metadata through two sources; the actual coordinator/evaluator returned both cards. Cross-source identity reconciliation remains unfixed.

## Evidence and reproduction

- [Combined latest results](evidence/latest-full-test.json)
- [Application case results](evidence/results.json)
- [12 browser observations](evidence/browser-checks.json)
- [Live model and Kaggle summary](evidence/live-integrations/summary.json) with timestamped case logs
- [Database check](evidence/full-recheck-database.json)
- [Supplemental duplicate/ranking results](evidence/supplemental-validation.json)

From the repository root, use the backend environment to run `docs/fix-verification/run_retests.py`, `docs/fix-verification/run_supplemental_validation.py` and, after quota reset, `docs/fix-verification/run_live_integrations.py`. Original assessment evidence remains preserved. SMTP and group/individual submissions stay excluded at the user's request.

## Fresh repeated test — 5 October 2026

The repeated run again passed all **69 application cases**, **12 manual Chrome checks**, frontend lint/types/production build, backend compilation/dependency checks and encrypted database readback/idempotent migration. The four seed-ranking smoke cases passed again. Authenticated Kaggle returned 3 datasets, and OpenML and Hugging Face returned 2 each for the smoke query. The working database remained unchanged.

The duplicate case still failed: the same dataset URL returned 2 cards instead of 1. One fresh Gemini preflight returned `429 RESOURCE_EXHAUSTED` for the daily free-tier limit of 20, with a provider retry delay of 27,375 seconds at observation (about 7 hours 36 minutes). The 15 live attack cases were **not rerun** after that preflight; the earlier blocked attempt above is historical evidence. No additional model resistance passes are claimed.

All synthetic browser users were signed out, password saving declined, the test tab closed and temporary servers stopped. Logs also reported a THREE.Clock deprecation and a shutdown semaphore warning; neither prevented the verified flows. This remains finite manual Chrome coverage and four project-authored ranking examples, not comprehensive browser or ranking certification. SMTP and group/individual submissions remain excluded.

- [Fresh combined results](evidence/repeat-full-test.json)
- [Fresh application results](evidence/repeat-application-results.json)
- [Fresh browser observations](evidence/repeat-browser-checks.json)
- [Fresh Gemini response](evidence/repeat-provider-check.json)
- [Fresh Kaggle result](evidence/repeat-kaggle-check.json)
- [Fresh OpenML / Hugging Face results](evidence/repeat-external-check.json)
- [Fresh database verification](evidence/repeat-database-check.json)
