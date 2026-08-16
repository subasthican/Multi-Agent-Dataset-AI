# Member 3 — Frontend & UX

See [`docs/members.md`](../../../docs/members.md) for context and the source
report's design direction.

## Setup

```bash
cd frontend/dataset-ai-ui
npm install
npm run dev
```

## Status

| File | Status |
|---|---|
| `Navbar.tsx` | **Done** — auth-aware (Sign In/Sign Up vs. profile link) |
| `SearchBox.tsx` | **Done** — calls `services/api.ts` `discover()` |
| `DatasetCard.tsx` | **Done** — name, domain/task, source badge, score bar, explanation |
| `AgentFlow.tsx` | **Done** — live NLP → Discovery → Evaluation stage visualization |
| `LoadingAnimation.tsx` | **Done** |
| `ExplanationCard.tsx` | **Done** — shows NLP understanding + llm/rule-based source |
| `GalaxyBackground.tsx` | **Done** — rotating 3D starfield (`@react-three/fiber` + drei) |
| `AuthCard.tsx` | **Done** — shared wrapper for login/register/forgot/reset pages |
| `../services/api.ts` | **Done** — typed client, `NEXT_PUBLIC_API_BASE_URL`-configurable |
| `../app/page.tsx` | **Done** — search + results assembled here (there's no separate `/dashboard`) |
| `../app/{login,register,forgot-password,reset-password,profile,pricing}/page.tsx` | **Done** |

Nothing left stubbed on the frontend. Open items are backend-side (Member 2's
`input_filter.py`/`encryption.py`/`responsible_ai/*` and search quota
enforcement for the Pro tier) — see `docs/members.md` and
`backend/security/README.md`.

Theme tokens live in `app/globals.css` (`.glass`, `.text-gradient`, the
`nebula-*` colors) — reuse those rather than hardcoding colors inline.
