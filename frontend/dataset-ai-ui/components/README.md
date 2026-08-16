# Member 3 — Frontend & UX

Scaffolding only — stub components, no implementation. See
[`docs/members.md`](../../../docs/members.md) for the full task list and the
"AI Galaxy Data Explorer" design direction from the source report.

## Setup

```bash
cd frontend/dataset-ai-ui
npm install framer-motion lucide-react
```

## Files to implement

| File | Purpose |
|---|---|
| `Navbar.tsx` | Site navbar |
| `SearchBox.tsx` | Query input, calls `services/api.ts` |
| `DatasetCard.tsx` | One recommended dataset |
| `AgentFlow.tsx` | NLP → IR → Evaluation agent activity visualization |
| `LoadingAnimation.tsx` | In-flight request state |
| `ExplanationCard.tsx` | Responsible AI explanation display |
| `../services/api.ts` | Typed API client (env-configured base URL) |
| `../app/dashboard/page.tsx` | Dashboard page wiring the above together |

Keep colors/theme tokens in `app/globals.css` rather than hardcoded inline
styles, so the space theme stays consistent across components.
