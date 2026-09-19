# Personal Opportunity Radar Backend

FastAPI service for the live career assistant. It owns the OpenRouter API key and exposes a normalized chat API for the Next.js frontend.

## Local setup

```bash
cd backend/openrouter
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
cp .env.example .env
```

Add an OpenRouter key to `.env` to enable live responses:

```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
```

Without a key, the API runs in demo mode with deterministic opportunity data.

## Run

```bash
cd backend/openrouter
uvicorn app.main:app --reload --port 8000
```

Endpoints:

- `GET /health`
- `POST /api/chat`

The chat endpoint accepts JSON requests with `prompt` and `messages`, or multipart requests with those fields plus an optional PDF. PDF text extraction is intentionally not enabled yet; the first milestone validates and receives the file boundary.

## Frontend connection

The Next.js app proxies browser requests through its own `/api/chat` route. Set this in `frontend/.env.local` when running the backend separately:

```env
BACKEND_URL=http://localhost:8000
```
