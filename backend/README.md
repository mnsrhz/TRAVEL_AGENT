# Travel Concierge Backend

FastAPI backend for the Travel Concierge Agent. It exposes the LangGraph-style workflow as HTTP endpoints for the React frontend.

## Local Run

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Render

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Set the API keys in Render environment variables:

- `OPENAI_API_KEY`
- `SERPAPI_API_KEY`
- `TAVILY_API_KEY`
- `GOOGLE_MAPS_API_KEY`
- `OPENAI_MODEL`
- `ALLOW_DEMO_FALLBACKS`
- `FRONTEND_ORIGIN`

