# Personal Opportunity Radar Documentation

## Run Locally

Start the backend and frontend in separate terminal windows.

### 1. Start the backend

From the repository root:

```bash
cd backend/openrouter
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

The backend provides:

- Health check: `http://localhost:8000/health`
- Chat API: `http://localhost:8000/api/chat`

Before starting the backend, copy the environment template if needed:

```bash
cd backend/openrouter
cp .env.example .env
```

Add your OpenRouter key to `backend/openrouter/.env`:

```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
```

Without an API key, the backend runs in demo mode with deterministic sample opportunities.

### 2. Start the frontend

In a second terminal, from the repository root:

```bash
cd frontend
npm install
```

Create `frontend/.env.local` if it does not exist:

```env
BACKEND_URL=http://localhost:8000
```

Then start Next.js:

```bash
npm run dev
```

Open the app at [http://localhost:3000](http://localhost:3000).

The browser sends chat requests to the Next.js `/api/chat` route, which proxies them to the FastAPI backend. The OpenRouter API key must remain in the backend environment and must not be added to frontend variables beginning with `NEXT_PUBLIC_`.

### Useful checks

```bash
curl http://localhost:8000/health
```

```bash
cd backend/openrouter
.venv/bin/pytest -q
```

```bash
cd frontend
npm run lint
npm run build
```