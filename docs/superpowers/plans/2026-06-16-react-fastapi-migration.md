# React FastAPI Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Vercel-ready React/Next.js frontend and Render-ready FastAPI backend that preserves the interactive HTML blueprint screens while reusing the existing travel concierge graph.

**Architecture:** Keep the current Streamlit app intact. Add `backend/` as an API facade over the existing `src` graph/state/tools and `frontend/` as a blueprint-aligned Next.js app that calls the API by session id.

**Tech Stack:** FastAPI, Uvicorn, existing Python graph modules, Next.js, React, TypeScript, CSS copied/adapted from `travel_concierge_interactive.html`.

---

### Task 1: Backend Session API

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/session_store.py`
- Create: `backend/app/schemas.py`
- Create: `backend/requirements.txt`
- Create: `backend/README.md`
- Create: `tests/test_backend_api.py`

- [x] **Step 1: Write failing backend API tests**

Create tests that call `/health`, create a session, submit chat, approve gates, and verify trace/state fields.

- [x] **Step 2: Implement backend models and session store**

Use an in-memory plus JSON-file session store under `backend/data/sessions` so Render can preserve state while the instance is alive and local development can inspect state.

- [x] **Step 3: Implement FastAPI endpoints**

Expose `/api/sessions`, `/api/sessions/{session_id}`, `/api/sessions/{session_id}/chat`, `/api/sessions/{session_id}/approve`, `/api/sessions/{session_id}/exports/itinerary.md`, and `/api/sessions/{session_id}/exports/calendar.ics`.

- [x] **Step 4: Verify backend tests**

Run `pytest tests/test_backend_api.py -q`.

### Task 2: Frontend Blueprint UI

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/next.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/page.tsx`
- Create: `frontend/app/globals.css`
- Create: `frontend/lib/api.ts`
- Create: `frontend/lib/types.ts`
- Create: `frontend/README.md`

- [x] **Step 1: Port CSS and screen anatomy**

Use the interactive HTML blueprint as the contract: shell, sidebar, onboarding screen, research progress, approval screens, itinerary, critique, calendar preview, export success, and reasoning cards.

- [x] **Step 2: Wire screen routing to backend state**

Map `COLLECTING_REQUIREMENTS`, `RESEARCHING`, approval states, itinerary states, calendar states, and `COMPLETE` to frontend screen indexes.

- [x] **Step 3: Wire buttons to API calls**

Chat submits call `/chat`; approval buttons call `/approve`; download buttons use export endpoints.

- [x] **Step 4: Add deployment documentation**

Document Vercel `NEXT_PUBLIC_API_BASE_URL` and Render backend env vars.

### Task 3: Repository Verification

**Files:**
- Modify: `README.md`
- Test: existing Python tests

- [x] **Step 1: Run backend and existing tests**

Run `pytest -q`.

- [x] **Step 2: Compile Python files**

Run `python -m py_compile backend/app/main.py backend/app/session_store.py backend/app/schemas.py`.

- [ ] **Step 3: Commit and push**

Stage only migration files and docs, not local secrets or source reference folders.
