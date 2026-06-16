# Travel Concierge Frontend

Next.js frontend that follows the interactive HTML prototype and calls the FastAPI backend.

## Local Run

```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## Vercel

- Framework preset: Next.js
- Root directory: `frontend`
- Build command: `npm run build`
- Output: default Next.js

Set this environment variable in Vercel:

- `BACKEND_API_BASE_URL`: your Render backend URL, for example `https://travel-agent-api.onrender.com`

The app calls same-origin `/api/...` routes in Vercel, and those routes proxy requests to the FastAPI backend.
