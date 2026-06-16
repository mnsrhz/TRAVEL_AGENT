# Travel Concierge Agent

A Streamlit-hosted Travel Concierge Agent for planning multi-city trips with approval gates, live travel research adapters, demo fallback data, itinerary export, calendar export, and an agent trace console.

The first release follows the approved design direction: polished Streamlit UI, modular agent/tool code, five approval gates from the requirements document, and a single fallback flag that controls whether missing or failed live APIs may use demo data.

## What It Does

- Collects destination, dates, duration, origin, budget, pace, and dietary preferences.
- Normalizes preferences and pauses at approval gates.
- Runs travel research through SerpAPI, Tavily, Google Places, and Google Maps adapters.
- Uses demo/mock travel data only when `ALLOW_DEMO_FALLBACKS=true`.
- Builds and reviews a day-by-day itinerary.
- Generates downloadable Markdown, ICS calendar, and trace JSON files.
- Shows workflow status, tool-call counts, token estimates, and recent agent reasoning.

## Live Vs Fallback Mode

`ALLOW_DEMO_FALLBACKS` is the release switch:

- `false` or omitted: strict live mode. Missing keys or live tool failures stop the workflow.
- `true`: live plus fallback mode. The app tries live tools when keys are present and uses labeled demo data when keys are missing or live calls fail.

For demos, set `ALLOW_DEMO_FALLBACKS=true`. For production validation, omit it or set it to `false`.

## Local Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/streamlit run streamlit_app.py
```

Streamlit reads secrets from environment variables or `st.secrets`. If you use a local `.env`, export the variables before starting Streamlit or set them in `.streamlit/secrets.toml`.

## Streamlit Cloud Deployment

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
.venv/bin/pytest -q
env PYTHONPYCACHEPREFIX=/private/tmp/travel-agent-pycache .venv/bin/python -m py_compile streamlit_app.py src/ui/styles.py src/ui/components.py src/config/settings.py
```

## Current Release Notes

- The modular tool adapters are ready for live APIs, with fallback policy enforced centrally.
- The itinerary generator is deterministic for the first release so demos remain stable.
- File-system memory is currently session-local through Streamlit state plus downloadable trace/export files. Persistent user memory can be added later behind an explicit storage boundary.
