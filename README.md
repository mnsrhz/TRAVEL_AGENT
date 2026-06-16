# Travel Concierge Agent

A Travel Concierge Agent for planning multi-city trips with approval gates, live travel research adapters, demo fallback data, itinerary export, calendar export, and an agent trace console.

The current app direction is a React/Next.js frontend hosted on Vercel with a FastAPI backend hosted on Render. The Streamlit app remains in the repo as a legacy/local reference path, but the production UI now follows the interactive HTML blueprint more closely: eight workflow screens, tool activity states, approval gates, chat-first intake, and a reasoning trace panel.

## What It Does

- Collects destination, dates, duration, origin, budget, pace, and dietary preferences.
- Normalizes preferences and pauses at approval gates.
- Runs travel research through SerpAPI, Tavily, Google Places, and Google Maps adapters.
- Uses demo/mock travel data only when `ALLOW_DEMO_FALLBACKS=true`.
- Builds and reviews a day-by-day itinerary.
- Generates downloadable Markdown, ICS calendar, and trace JSON files.
- Shows workflow status, tool-call counts, token estimates, and recent agent reasoning.

## Architecture

- `frontend/`: Next.js app for Vercel. It renders the approved interactive UI blueprint and calls the backend API.
- `backend/`: FastAPI service for Render. It exposes session, chat, approval, and export endpoints.
- `src/`: shared agent, tool, state, export, and workflow logic.
- `streamlit_app.py`: legacy Streamlit entrypoint retained for local comparison.

## Live Vs Fallback Mode

`ALLOW_DEMO_FALLBACKS` is the release switch:

- `false` or omitted: strict live mode. Missing keys or live tool failures stop the workflow.
- `true`: live plus fallback mode. The app tries live tools when keys are present and uses labeled demo data when keys are missing or live calls fail.

For demos, set `ALLOW_DEMO_FALLBACKS=true`. For production validation, omit it or set it to `false`.

## Local Setup - React + FastAPI

Start the backend:

```bash
.venv/bin/pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

Start the frontend in another terminal:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Open `http://localhost:3000`.

## Render Backend Deployment

Create a Render Web Service from this GitHub repo:

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Set these Render environment variables:

```text
OPENAI_API_KEY=...
SERPAPI_API_KEY=...
TAVILY_API_KEY=...
GOOGLE_MAPS_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
ALLOW_DEMO_FALLBACKS=true
FRONTEND_ORIGIN=https://your-vercel-app.vercel.app
```

For strict live mode, set `ALLOW_DEMO_FALLBACKS=false`.

## Vercel Frontend Deployment

Create a Vercel project from this GitHub repo:

- Framework preset: Next.js
- Root directory: `frontend`
- Build command: `npm run build`

Set this Vercel environment variable:

```text
BACKEND_API_BASE_URL=https://your-render-service.onrender.com
```

The frontend includes a same-origin `/api/...` proxy route, so browser requests go to Vercel first and Vercel forwards them to Render. `NEXT_PUBLIC_API_BASE_URL` is still supported for direct browser calls, but `BACKEND_API_BASE_URL` is preferred because it avoids CORS and keeps the backend URL server-side.

After Vercel gives you the public URL, update Render's `FRONTEND_ORIGIN` to match it.

## Legacy Streamlit Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/streamlit run streamlit_app.py
```

Streamlit reads secrets from environment variables or `st.secrets`. If you use a local `.env`, export the variables before starting Streamlit or set them in `.streamlit/secrets.toml`.

## Legacy Streamlit Cloud Deployment

1. Push this repository to GitHub.
2. In Streamlit Cloud, create a new app from the repo.
3. Set the app entrypoint to `streamlit_app.py`.
4. Add secrets in Streamlit Cloud using the shape from `.streamlit/secrets.toml.example`.
5. Deploy.

Required production secrets:

```toml
OPENAI_API_KEY = "..."
SERPAPI_API_KEY = "..."
TAVILY_API_KEY = "..."
GOOGLE_MAPS_API_KEY = "..."
ALLOW_DEMO_FALLBACKS = "false"
```

For a public demo while API access is still being configured:

```toml
ALLOW_DEMO_FALLBACKS = "true"
```

## Verification

```bash
.venv/bin/pytest tests/test_backend_api.py -q
cd frontend && npm run build
.venv/bin/pytest -q
env PYTHONPYCACHEPREFIX=/private/tmp/travel-agent-pycache .venv/bin/python -m py_compile streamlit_app.py src/ui/styles.py src/ui/components.py src/config/settings.py
```

## Current Release Notes

- The modular tool adapters are ready for live APIs, with fallback policy enforced centrally.
- The itinerary generator is deterministic for the first release so demos remain stable.
- File-system memory is currently session-local through Streamlit state plus downloadable trace/export files. Persistent user memory can be added later behind an explicit storage boundary.
