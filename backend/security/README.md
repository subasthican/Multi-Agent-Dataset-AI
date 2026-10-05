# Member 2 — Security & Responsible AI

[`docs/members.md`](../../docs/members.md) has the full task list and context.

## Setup

```bash
pip install -r ../requirements.txt
```
Auth deps: `sqlalchemy`, `bcrypt`, `pyjwt`, `email-validator`.

Set `JWT_SECRET_KEY` in the repo-root `.env` for a persistent signing secret
(see `../.env.example`) — without it, a random one is generated at process
start and existing tokens stop working on every restart.

## Status

| File | Status |
|---|---|
| `db.py`, `db_models.py` | **Done** — SQLite via SQLAlchemy (`database/app.db`, gitignored) |
| `jwt_manager.py` | **Done** — password-bound PyJWT access tokens; password changes/recovery invalidate old tokens |
| `authentication.py` | **Done** — bcrypt hashing, `get_current_user` dependency |
| `password_reset.py`, `schemas.py`, `router.py` | **Done** — register/login/me/change-password/forgot-password/reset-password |
| `admin_router.py` | **Done** — `/admin/users` (list w/ search+filter+sort, detail, patch, delete), `/admin/catalog` CRUD, `/admin/plans` CRUD |
| `db_models.py` (`Plan`, `SearchUsage`) + `plan_seed.py` + `usage_limits.py` | **Done** — plans are a DB table (admin-editable, not hardcoded), and `daily_search_limit` is actually enforced server-side across discovery and standalone AI routes, with atomic history-independent counters and HMAC-protected anonymous identifiers |
| `input_filter.py` | Implemented heuristic guards; finite coverage, not universal injection protection |
| `encryption.py` | Authenticated encryption integrated into stored query text; legacy history migrated; persistent key required |
| `../responsible_ai/explainability.py` | Implemented heuristic score disclosure |
| `../responsible_ai/fairness.py` | Implemented source/domain representation diagnostics; not fairness certification |
| `../responsible_ai/privacy.py` | Implemented email/phone-pattern redaction before prompt/history handling |

## Auth API

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /auth/register` | — | `{name, email, password}` -> `{access_token}` |
| `POST /auth/login` | — | `{email, password}` -> `{access_token}` |
| `GET /auth/me` | Bearer | Current user |
| `PATCH /auth/me` | Bearer | Update name |
| `POST /auth/change-password` | Bearer | `{current_password, new_password}` |
| `POST /auth/forgot-password` | — | `{email}` -> generic message only; capability delivered privately through configured SMTP |
| `POST /auth/reset-password` | — | `{token, new_password}` — single-use, expires in 30 min |

SMTP delivery code is implemented. Configuration and live delivery verification are deferred at the user's request. Reset tokens are never returned publicly and only their digests are stored.

Search/discovery stays open without login — accounts are additive (profile,
`plan` field for the commercialization tiers in `docs/members.md` /
`frontend/dataset-ai-ui/app/pricing`). Plans are DB-backed and admin-editable
(`/admin/plans`), and each plan's `daily_search_limit` is enforced
server-side in `usage_limits.py`, checked before discovery and standalone AI routes run
— including for anonymous callers, tracked by a keyed hash of the peer address. See
`docs/admin-panel-roadmap.md` Phase 3 for the full writeup.

## Admin API

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET/PATCH/DELETE /admin/users`, `/admin/users/{id}` | Admin | List (search/filter/sort via query params)/detail (+ search history)/update plan, admin, active status/delete |
| `GET/POST/PATCH/DELETE /admin/catalog`, `/admin/catalog/{id}` | Admin | Curated dataset catalog CRUD |
| `GET/POST/PATCH/DELETE /admin/plans`, `/admin/plans/{id}` | Admin | Pricing tier CRUD |
| `GET /admin/stats` | Admin | Dashboard counters |
| `GET /plans`, `GET /usage` | — (usage: optional token) | Public — pricing page and "searches left today" badge |

**Implemented:** administrative mutations create transactional audit records, available to admins through `GET /admin/audit` and the frontend activity page. User/catalog/plan DELETE requests require the current password in their JSON body; failures are logged without credentials and throttled. Audit records survive account deletion. They are not protected against direct database-owner modification.

See [security report](../../docs/security.md) and [verified checks](../../docs/fix-verification/README.md).

`DATA_ENCRYPTION_KEY` must be persistent and backed up securely. Query text is encrypted; ordinary account metadata and domain/task labels remain outside this field-encryption scope.
