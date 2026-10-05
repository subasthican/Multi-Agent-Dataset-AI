# Deploy the backend and frontend as two Vercel projects

Local deployment preparation is tested. No hosted Neon database or Vercel deployment has been created or verified by these checks. SMTP stays excluded.

## 1. Create the hosted database

1. Open [Neon](https://neon.com/) and sign in.
2. Create a project named `dataset-ai`. Choose a database region near your intended backend region.
3. Open **Connect**, select the intended branch/database/role, and enable **connection pooling**.
4. Copy the **connection string**, starting with `postgresql://`. Keep its `sslmode=require` and any provider-supplied options. Copy the URL itself, without the surrounding `psql` command or quotes.
5. Save it in the backend Vercel project's `DATABASE_URL` environment variable. It contains a database password; keep it in environment settings rather than source code or chat.

Neon's [connection guide](https://github.com/neondatabase/website/blob/main/content/docs/get-started/connect-neon.md) describes the Connect dialog and pooled URLs. A separate Neon account/project can be created before importing the Vercel backend. A Vercel Marketplace database integration is an alternative, not an additional database requirement.

The hosted database starts fresh. Startup creates the application tables, ten catalog entries and three plans. Local accounts, edited catalog entries and history are not automatically copied. Register an account again for the cloud application. A migration of existing local data is separate work.

## 2. Make the prepared files available to Vercel

Commit and push the repository changes to the GitHub branch connected to Vercel. Review/select the prepared source/configuration/documentation files in your IDE's Source Control view. The root `.env`, SQLite database and generated `backend/model_assets/` stay ignored.

The backend changes provide PostgreSQL/psycopg URL support, safe concurrent schema/seeding, offline model packaging, fresh catalog snapshots across function instances and platform client-IP quota handling. Vercel already recognizes `backend/main.py` once `backend` is the project root; no second Python wrapper is needed.

## 3. Import the backend

On the screen in your screenshot, choose **Import single project** next to **backend**.

| Setting | Value |
|---|---|
| Project name | `dataset-ai-backend` or another available name |
| Root directory | `backend` |
| Framework/application preset | FastAPI |
| Python version | 3.12, selected by `backend/.python-version` |
| Build command | `python scripts/build_models.py`, configured by `backend/vercel.json` |
| Output directory | Leave the FastAPI default |

The build installs the compatible English spaCy model and saves MiniLM under `model_assets/embeddings`, then verifies an offline load. Linux uses the pinned CPU-only PyTorch wheel. The function configuration includes those generated model assets and allows 120 seconds per invocation.

In **Environment Variables**, add these for the environments you intend to deploy:

| Backend variable | Value |
|---|---|
| `DATABASE_URL` | Your Neon pooled PostgreSQL connection string |
| `DATA_ENCRYPTION_KEY` | The persistent Fernet key already configured in your local root `.env` |
| `JWT_SECRET_KEY` | The persistent signing secret already configured in your local root `.env` |
| `GEMINI_API_KEY` | Your locally configured Gemini key |
| `KAGGLE_API_TOKEN` | Your locally configured Kaggle token |
| `VERCEL_SUPPORT_LARGE_FUNCTIONS` | `1` |
| `ALLOWED_ORIGINS` | Your exact intended frontend HTTPS origin; update it to the actual URL after frontend deployment |

Do not add a `NEXT_PUBLIC_` prefix to backend credentials. Vercel sets `VERCEL=1` itself. The app will reject missing/SQLite database configuration and a missing JWT secret in that runtime; the encryption key is always required. Set model overrides only if you deliberately want the build to package a different compatible model.

The AI stack exceeds the standard Python bundle size on the local machine. Enable large functions for this backend: Vercel documents Python bundles up to 5 GB in its [large-functions beta](https://vercel.com/docs/functions/limitations#large-functions-beta). The actual Linux bundle size and platform compatibility remain to be checked by the hosted build. If large functions are unavailable or the hosted build fails, use a Python container host for the backend; a 500 MB standard function bundle is not the expected route for this stack.

Click **Deploy** after the database/environment values and pushed source are present. Resolve any build error before proceeding to the frontend. Copy the actual assigned backend HTTPS URL; the project name alone does not guarantee a particular domain.

Open `<backend-url>/`, `<backend-url>/plans` and `<backend-url>/docs`. The root should return the application message and plans should return the three seeded tiers. These initial checks do not prove every feature works.

## 4. Import the frontend

Create another Vercel project from the same repository, choosing **Import single project** beside **dataset-ai-ui**.

| Setting | Value |
|---|---|
| Root directory | `frontend/dataset-ai-ui` |
| Framework | Next.js |
| Build command | Default `npm run build` |
| `NEXT_PUBLIC_API_BASE_URL` | The actual backend HTTPS URL, without a trailing slash or an extra `/api` prefix |

Deploy. Copy its actual frontend origin, such as `https://your-frontend.vercel.app`, into the backend's `ALLOWED_ORIGINS` and redeploy the backend. The value is an origin without a path/trailing slash; multiple exact allowed origins are comma-separated. Preview domains need explicit matching configuration if you want previews to call the backend.

`NEXT_PUBLIC_API_BASE_URL` is a browser-visible build-time setting. If you change it later, rebuild/redeploy the frontend. The current [Next.js environment guide](https://nextjs.org/docs/pages/guides/environment-variables) explains that behavior.

## 5. Verify the hosted application

Check registration/login, pricing, a diabetes search, a property/house-price query, search history and sign-out. Confirm history survives a new session/deployment and different anonymous clients have appropriate quota counters. Check admin catalog updates appear in a new browser session/function instance.

For initial administrator access, register your own account first. In your own Neon project's SQL Editor, replace the placeholder with that registered email and run:

```sql
UPDATE users SET is_admin = TRUE WHERE email = 'your-own-email@example.com';
```

Verify exactly your intended account was updated, then sign in again. This is an owner-performed bootstrap; there is no public administrator creation endpoint. The app's ordinary admin actions are audited afterward. Avoid the local demo `seed_admin.py` defaults for the hosted app.

Gemini may still use rule-based fallback when its provider quota/service is unavailable. Deploying does not replenish that quota. Real password reset delivery is unavailable while SMTP remains unconfigured, as requested.

## Local evidence

The prepared source passed 69 existing application cases, 32 unit cases and 22 focused PostgreSQL cases. The PostgreSQL tests used a disposable local PostgreSQL 15 server, synthetic accounts, declared provider fixtures and the actual bundled embedding model under `VERCEL=1`. They verified concurrent startup, shared catalog freshness, encrypted history, JWT revocation, reset capability consumption, admin password controls/audit, concurrent quotas and separate platform-IP usage. The working SQLite file was unchanged.

The model build produced 91,588,813 bytes of embedding assets and loaded them offline. These checks establish local preparation, not a successful Linux/Vercel deployment or a real Neon connection. See [deployment preparation evidence](fix-verification/evidence/vercel-preparation.json) and [PostgreSQL case details](fix-verification/evidence/postgres-validation.json).

Official references: [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi), [function limits](https://vercel.com/docs/functions/limitations), [Vercel client headers](https://vercel.com/docs/headers/request-headers), [SQLAlchemy PostgreSQL/psycopg](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html).
