# Admin Panel Roadmap

**Status: Phases 1-3 done, Phases 4-5 planned but not built.** Written so a
new chat with zero memory of this conversation can pick up exactly where it
left off — read this whole file before touching any admin code.

## How this project actually works (read this first)

- **Branch-per-member workflow.** Backend security/DB/catalog work goes on
  `member2-security-agent`. Frontend UI work goes on `member3-frontend-ui`.
  Cross-cutting docs go on `member1-nlp-agent`. Every change: commit on the
  right branch → push → merge `--no-ff` into `dev` → merge `dev` into `main`
  → push `main`. See `docs/members.md` for the full reasoning (this is a
  university group assignment; commits need to reflect who owns what).
- **Local full-stack testing across two branches**: since backend and
  frontend work happen on different branches, to test both together locally,
  `git merge --no-ff origin/<other-branch> -m "TEMP local merge for
  full-stack testing (will not push)"`, test, then `git reset --hard
  <last-real-commit>` before pushing — never push the temp merge.
- **SQLite has no migrations.** Any DB schema change (new column/table)
  means deleting `database/app.db` and letting `init_db()` recreate it fresh
  on next startup — this wipes all local test data. Always mention this to
  the user when it happens.
- **Always verify live, not just written.** Every phase so far has been
  tested with real curl calls and/or real browser interaction (via the
  Claude Browser tools), not just "should work." Keep doing that.
- **After each phase**: update `docs/agent-improvements.md` (new
  fixed/open items) and `docs/members.md` if setup steps changed, same as
  every prior phase.
- Restart the backend after any code change:
  `pkill -f "uvicorn main:app"; cd backend && uvicorn main:app --reload --port 8000`
  (background it, check `/tmp/uvicorn_*.log` for errors).

## Why this roadmap exists

The admin panel started as a bare user list (Phase 1). The user asked what a
*genuinely commercialized* SaaS product's admin panel would need, and picked
this order to build it in.

---

## Phase 1 — Foundation ✅ DONE

**What:** `User.is_admin` field, `get_current_admin_user` dependency (403s
non-admins), `scripts/promote_admin.py` (bootstrap script, not an API
endpoint — deliberate, avoids a privilege-escalation hole), basic
`/admin/users` (list/patch-plan/patch-admin/delete) and `/admin/stats`.

**Files:** `backend/security/db_models.py` (`User.is_admin`), `authentication.py`
(`get_current_admin_user`), `admin_router.py`, `scripts/promote_admin.py`.
Frontend: `app/admin/page.tsx`, `Navbar.tsx` (Admin link), `services/api.ts`
(`AdminUser`, `AdminStats`, admin functions).

**Why it mattered:** there was no way for any account to ever become "pro" —
no billing existed. This is genuinely how plan changes happen today.

## Phase 2 — Dataset Catalog Management ✅ DONE

**What:** catalog moved from a static `datasets.json` file into a DB table
(`CatalogDataset`), full CRUD via `/admin/catalog`, a real cache-invalidation
fix so admin edits show up in live search immediately (the FAISS index used
to be cached forever via `@lru_cache`, which would've made this silently
broken without the fix).

**Files:** `backend/security/db_models.py` (`CatalogDataset`),
`agents/discovery_agent/seed.py` (one-time migration, never overwrites
admin changes), `agents/discovery_agent/vector_store.py` (`invalidate_cache()`),
`agents/discovery_agent/models.py` (`CatalogDataset{Create,Update,Response}`),
`admin_router.py` (`/admin/catalog` CRUD + `catalog_size` stat). Frontend:
`app/admin/catalog/page.tsx`, linked from `/admin`.

**Verified live:** added "Space Weather Dataset" through the actual UI form,
confirmed it was immediately the top live search result with zero restart.

---

## Phase 3 — Plan Management + Real Limit Enforcement ✅ DONE

**What:** plans moved from a hardcoded `TIERS` array into a DB table
(`Plan`), full CRUD via `/admin/plans`, and — the part that actually makes
"free" vs "pro" mean something — a real daily search-limit check that runs
*before* `/discover`'s pipeline executes. Anonymous callers get the Free
plan's limit too, tracked by IP (a decision explicitly confirmed with the
user rather than assumed): 10 searches/day for Free, unlimited for
Pro/Enterprise, and admins can create arbitrary custom plans (a "Student"
plan at $5/month, 50/day was created live during testing to prove this
isn't hardcoded to just two tiers).

**Files:** `backend/security/db_models.py` (`Plan`, `AnonymousSearchLog`),
`security/plan_seed.py` (seeds the 3 original tiers once, same
seed-if-empty pattern as the catalog), `security/usage_limits.py`
(`enforce_search_limit`, `get_usage`, `record_anonymous_search`),
`security/schemas.py` (`Plan{Create,Update,Response}`, `UsageResponse` —
note `PlanUpdateRequest.clear_search_limit`, a dedicated flag added because
a plain `Optional[int] = None` on a PATCH body can't distinguish "field not
sent" from "field explicitly cleared"), `admin_router.py` (`/admin/plans`
CRUD — rename is blocked, delete is blocked while any user is still on that
plan), `main.py` (`enforce_search_limit()` call at the top of `/discover`,
new public `GET /plans` and `GET /usage` endpoints).

Frontend: `app/admin/plans/page.tsx` (new, mirrors `admin/catalog/page.tsx`'s
inline add/edit/delete pattern exactly as planned below), `pricing/page.tsx`
(rewritten to fetch `GET /plans` instead of the old hardcoded array, with
honest CTAs — no fake self-upgrade button since billing still isn't wired
to a payment provider), `app/page.tsx` (a "X of N searches left today"
badge next to the search box via `GET /usage`, and the existing error
banner now also carries the 429 message so a hit limit is never silent),
`app/admin/page.tsx` (the old free/pro toggle is now a `<select>` populated
from real plans), `services/api.ts` (`Plan`/`Usage` types + plan API
functions; `User.plan` widened from a `"free" | "pro"` union to `string`
since plans are dynamic now).

**Verified live:** curl-tested the full backend surface (10-then-429
enforcement, Pro bypassing the limit, a custom plan with a real 50/day cap
enforced, delete blocked while in use, duplicate-name 409, the
clear-limit PATCH flag flipping a set limit back to unlimited) *and*
separately verified the frontend against a running backend in the browser
— the pricing page renders the real seeded tiers, a 429 renders as a
visible error banner (reproduced by exhausting the anonymous IP's quota
via the UI, not just curl), a plan created/edited through the new admin UI
round-trips correctly to the pricing page, and the admin dashboard's plan
dropdown lists and applies all real plans including the custom one.

## Phase 4 — User Detail Page + Search/Filter ⬜ NEXT

The `/admin` user table is a flat list — fine at a handful of users, useless
beyond that.

**Backend:**
- `GET /admin/users/{id}` — single user detail: full profile +
  their actual search history (reuse the `SearchHistory` query pattern
  already in `recommendation_agent/agent.py`'s `_build_profile`, but return
  the raw list, not just the aggregated mode).
- Consider adding basic filtering/sorting to `GET /admin/users` (by plan,
  by signup date) via query params, rather than only ever returning everyone.

**Frontend:**
- `/admin/users/[id]/page.tsx` — profile info, plan/admin controls (move
  them here from the flat table, or keep both), a list/timeline of their
  searches.
- Search/filter/sort controls on the `/admin` user table itself.
- Link each table row's name to their detail page.

**Also consider (raised when the admin panel was first planned, not yet
decided):** suspend/disable instead of only hard-delete — a reversible
disable is safer for support situations than permanent deletion. Ask the
user whether this is in scope for this phase or later.

## Phase 5 — System Health + Audit Log ⬜ TODO

Two related but distinct gaps, both already flagged in
`docs/agent-improvements.md`:
- No visibility into whether Gemini/Kaggle/OpenML/HuggingFace are actually
  reachable right now — you only find out when a real search silently
  falls back.
- No audit log of admin actions (who changed what plan/catalog
  entry/admin status/deletion, when) — flagged as item #6 under Security/Auth
  in `agent-improvements.md`. No re-auth before destructive actions either
  (item #7, same section).

**Backend:**
- A lightweight health-check endpoint, e.g. `GET /admin/health` — try a
  trivial call to each external dependency (Gemini, Kaggle, OpenML,
  HuggingFace) with a short timeout and report up/down + latency. Careful:
  don't spam these APIs on every dashboard load — consider caching the
  health check result for a minute or two rather than hitting live on every
  page view.
- An `AdminActionLog` table (admin_id, action, target, timestamp, maybe a
  JSON diff of what changed) — write a row from every mutating `/admin/*`
  endpoint (users PATCH/DELETE, catalog POST/PATCH/DELETE, plans
  CRUD once Phase 3 exists). Retrofit the earlier endpoints too, not just
  new ones.
- `GET /admin/audit-log` to list it (paginate — this table only grows).
- Re-auth for deletes: simplest version is requiring the admin's current
  password again on `DELETE /admin/users/{id}` (and catalog/plan deletes),
  not just an already-valid session token.

**Frontend:**
- `/admin/settings` (or fold health into `/admin`'s existing stat cards) —
  green/red indicators per external service.
- `/admin/audit-log` — a simple reverse-chronological table.
- A password-confirmation step in delete flows (modal asking for password,
  not just the existing `window.confirm()`).

---

## When all 5 phases are done

Update `docs/members.md`'s admin panel section and `docs/agent-improvements.md`
to reflect the final state — several currently-open items (no plan
enforcement, no audit log, no re-auth on delete) will move to Fixed. Don't
forget `docs/mid-evaluation/*.md` and the pptx deck if the commercialization
story materially changed (real enforced plan limits is a good, concrete
addition to the commercialization pitch).
