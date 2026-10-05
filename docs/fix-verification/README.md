# Application fixes and verification

**Current fixes:** [Duplicate reconciliation fixed; 69 application checks, 23 new unit tests, 38 ranking/abstention cases and 3 HTTP checks pass](remaining-fixes.md). Gemini daily quota and provider availability still block live evaluation. Earlier [full test attempts](latest-full-test.md) are preserved as historical evidence, including 12 manual browser passes.

## Current credential feedback

The latest locally configured Gemini key is accepted. A short request returned `OK`; a diagnostic `gemini-3.8-flash` request returned valid healthcare/classification/tabular JSON. The project's configured model remains `gemini-3.5-flash`; model overrides were test-only. Subsequent batches encountered 429 quota and repeated 503 high-demand responses, so live attack coverage is still incomplete. This is no longer the earlier leaked-key rejection. Authenticated Kaggle search returned three datasets. The application regression suite was rerun and all 69 cases passed. See [credential feedback](evidence/live-integrations/credential-feedback.json). Model calls/fixtures and interrupted runs are explicitly distinguished; no independent student completion is claimed.


Implemented at the user's request, following the preserved [baseline assessment](../individual-assessments/README.md). Student information and personal reflections are deferred as requested.

## Verified results

**69 PASS, 0 FAIL, 0 ERROR.** [Results](evidence/results.json) and [source hashes / manifest](evidence/manifest.json) record this run. A separate [migration check](evidence/migration.json) applied startup migration twice to an isolated copy of the existing database and preserved 4 users, 10 catalog entries and 26 history records. Tests left the working database unchanged. A subsequent authorized [local encryption migration](evidence/local-encryption-migration.json) encrypted its 26 history queries while preserving all row counts, after creating an encrypted backup.

| Scope | Cases | Result |
|---|---:|---|
| Privacy/authentication/history | 15 | All passed |
| Original adversarial inputs, tested against application guards | 15 | All rejected before provider call |
| Controlled malformed model outputs | 15 | All handled safely |
| Responsible AI / retrieval | 15 | All passed |
| Quotas, concurrency, unsafe URLs, recovery sessions, valid LLM output | 5 | All passed |
| Admin auditing, password confirmation and throttling | 3 | All passed |
| Authenticated history encryption and key failures | 1 | Passed |

Frontend lint, TypeScript checks and the production build passed on the latest rerun. See [final status](evidence/final-status.json). Backend compilation and dependency consistency checks passed. Tests use isolated SQLite storage, real spaCy, MiniLM and FAISS; remote generation and email delivery are replaced only where identified in evidence. A focused English/ranking regression check also returned the expected seed datasets after correcting two initial regressions.

## Implemented changes

- **Subasthican:** explicit input-override guards, untrusted request framing in prompts, strict allowlisted LLM output validation, bounded keyword lists and safe malformed-output fallback.
- **Gowsika:** generic reset responses, private SMTP reset delivery, digest-only stored capabilities, atomic single-use reset and outstanding-token invalidation, password-bound JWTs, contact redaction before prompts/history, independent atomic usage counters shared by all AI endpoints, HTTP(S)-only catalog links, transactional admin audit records, admin-only `/admin/audit` access and `/admin/audit` UI, plus password-confirmed user/catalog/plan deletion with throttling after five failed attempts in 15 minutes.
- **Kageepan:** specific intent/modality precedence, declared unsupported language/domain handling, verified catalog modality fields and compatibility filtering, normalized cosine similarity across retrieval sources, source-representation diagnostics, explicit discriminatory-request guards and clearer frontend score/privacy disclosures.

## Run locally

Install backend dependencies and the `en_core_web_sm` spaCy model, plus `httpx` for the harness, then run from the repository root:

```bash
python docs/fix-verification/run_retests.py
```

This writes only the separate fix-verification evidence. Original assessment logs remain archived; baseline runners refuse to overwrite them. Startup applies additive schema changes, minimizes email/phone patterns in legacy history and invalidates legacy plaintext reset tokens. Previously issued JWTs require a fresh login after upgrading. Back up the database before deploying this migration.

## Remaining configuration and limits

- **Gemini:** latest key accepted; full live tests now blocked by quota/availability, as detailed above.
- **Reset emails — deferred at user request:** SMTP configuration is skipped for now. For future use, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, optional credentials and `FRONTEND_URL` using [environment example](../../backend/.env.example). Actual SMTP delivery was not exercised.
- **Individual submissions:** student IDs, lecturer-confirmed allocations, each member's own reflection, independent reproduction and viva remain personal/institutional work. Draft notes and viva practice are supplied in the reports.
- Input guards and language detection are heuristics with finite coverage. Contact redaction targets email/phone patterns, not all personal data. Search text is encrypted at rest; account metadata and domain/task labels are not covered by this field encryption. Source counts and score parity are not population-level fairness certification. Unknown external modality is excluded for non-tabular requests; metadata still needs validation.
- External provider availability, deployment, TLS, payment integrations, retention policy and production-wide security are outside these passing checks. No 100% completion/security claim is made.

## Admin audit and deletion behavior

Successful user updates/deletes and catalog/plan create/update/delete actions store actor ID, action, target ID/type, timestamp and changed field names. Failed password confirmation stores a minimal failure event. Values, passwords, email addresses and search text are excluded. The application exposes no audit edit/delete endpoint; records survive account deletion. Database owners can still alter SQLite records, so this is not a tamper-proof external audit service. The viewer lists the latest 100 records (API limit at most 200); archival and retention policy remain deployment decisions.

Deleting a user, catalog entry or plan now requires a JSON body `{"password": "current admin password"}` in addition to the bearer token. Missing passwords return 422, incorrect passwords 403 and excessive failures 429. The frontend uses a masked password dialog and clears the entered value on close. Selected browser flows have now been manually verified in native Chrome; see the latest full attempt for scope and limitations.

## Search-history encryption

A persistent Fernet key is configured locally in the gitignored `.env`. New `search_history.query` values are authenticated ciphertext in SQLite, transparently decrypted for authorized ORM/API reads. Startup encrypts legacy plaintext after contact redaction and validates already-encrypted records; repeated startup does not rewrite unchanged ciphertext. Missing/invalid keys stop startup, and incorrect keys cannot read encrypted history. This protects query text, not the entire database or an authorized application's runtime access.

The [isolated migration evidence](evidence/encryption-migration.json) and [local migration receipt](evidence/local-encryption-migration.json) record preserved row counts. The pre-migration snapshot is itself Fernet-encrypted in the gitignored, restricted `database/private-backups/` directory. Keep a secure backup of `DATA_ENCRYPTION_KEY`; replacing or losing it makes both stored queries and encrypted backups unreadable. Rotation requires explicit decryption/re-encryption using both keys. Restart an already-running backend to load the new code and environment.

## Latest full review

See [full project recheck](../full-project-recheck.md) for fresh results, group/individual brief coverage and remaining implementation/submission gaps beyond this fix suite.

## Credential verification and live tests

After configuring keys locally, run `python docs/fix-verification/run_live_integrations.py`. Credentials are loaded from the gitignored root `.env` and omitted from saved evidence. Normal requests exercise real spaCy and Gemini analysis. Adversarial prompt tests deliberately bypass the input guard to examine the provider prompt/output boundary; actual application guard tests remain in the 69-case suite. New timestamped evidence runs preserve previous outcomes. Kaggle is tested directly to verify the authenticated integration rather than relying on another source's results. Requests are paced to reduce short-window throttling; pacing cannot restore an exhausted daily allowance. Provider/network/quota failures are recorded as BLOCKED, not resistance. Single samples cannot establish general model safety.
