# Member 2 — Security & Responsible AI

Scaffolding only — structure and TODOs, no implementation. See
[`docs/members.md`](../../docs/members.md) for the full task list and context.

## Setup

```bash
pip install python-jose passlib bcrypt cryptography
```

## Files to implement

| File | Purpose |
|---|---|
| `jwt_manager.py` | Issue/verify JWT tokens |
| `authentication.py` | FastAPI dependency enforcing auth on routes |
| `input_filter.py` | Sanitize/block malicious or prompt-injection input |
| `encryption.py` | Encrypt/decrypt sensitive stored data |
| `../responsible_ai/explainability.py` | Explain why a dataset was recommended |
| `../responsible_ai/fairness.py` | Bias/fairness check on results |
| `../responsible_ai/privacy.py` | Strip sensitive fields before logging/storage |

When wiring into `backend/main.py`, coordinate with Member 1 rather than editing
their NLP agent routes directly — open a PR into `dev` and review together.

Write up `docs/security.md` for the final report once implemented.
