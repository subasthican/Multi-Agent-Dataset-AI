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
| `jwt_manager.py` | **Done** — PyJWT access tokens |
| `authentication.py` | **Done** — bcrypt hashing, `get_current_user` dependency |
| `password_reset.py`, `schemas.py`, `router.py` | **Done** — register/login/me/change-password/forgot-password/reset-password |
| `input_filter.py` | TODO — sanitize/block malicious or prompt-injection input into the NLP agent's queries |
| `encryption.py` | TODO — encrypt/decrypt sensitive stored data (not yet needed — nothing sensitive beyond password hashes is stored) |
| `../responsible_ai/explainability.py` | TODO — separate from the Evaluation Agent's built-in explanation strings; could add a dedicated fairness/bias angle |
| `../responsible_ai/fairness.py` | TODO |
| `../responsible_ai/privacy.py` | TODO |

## Auth API

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /auth/register` | — | `{name, email, password}` -> `{access_token}` |
| `POST /auth/login` | — | `{email, password}` -> `{access_token}` |
| `GET /auth/me` | Bearer | Current user |
| `PATCH /auth/me` | Bearer | Update name |
| `POST /auth/change-password` | Bearer | `{current_password, new_password}` |
| `POST /auth/forgot-password` | — | `{email}` -> generic message + `dev_reset_token` (no email provider configured yet — see below) |
| `POST /auth/reset-password` | — | `{token, new_password}` — single-use, expires in 30 min |

**Email delivery isn't wired up.** `forgot-password` returns the reset token
directly in the response so the flow works end-to-end in development. Before
this goes anywhere real, swap that for an actual email send (SMTP/SendGrid/
etc.) and drop the `dev_reset_token` field.

Search/discovery stays open without login — accounts are additive (profile,
`plan` field for the commercialization tiers in `docs/members.md` /
`frontend/dataset-ai-ui/app/pricing`). Nothing currently enforces free-tier
usage limits server-side; that'd be the natural next step if you want the
Pro tier to mean something beyond a label.

Write up `docs/security.md` for the final report.
