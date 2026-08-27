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
| `../app/admin/{page,catalog/page,plans/page}.tsx`, `../app/admin/users/[id]/page.tsx` | **Done** — user management (search/filter/sort, detail + history, suspend/reactivate), catalog CRUD, plan CRUD |

Nothing left stubbed on the frontend. Open items are backend-side (Member 2's
`input_filter.py`/`encryption.py`/`responsible_ai/*`, an admin action audit
log, and re-auth before destructive admin actions) — see `docs/members.md`,
`backend/security/README.md`, and `docs/admin-panel-roadmap.md` Phase 5.

Theme tokens live in `app/globals.css` (`.glass`, `.text-gradient`, the
`nebula-*` colors) — reuse those rather than hardcoding colors inline.
