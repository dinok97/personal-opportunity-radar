# Personal Opportunity Radar Backend

FastAPI service for the live career assistant. It exposes a normalized chat API for the Next.js frontend and supports OpenRouter or Ollama as the LLM provider.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
cp .env.example .env
```

Set `LLM_PROVIDER` in `.env` to choose a provider. Ollama is the default:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen3.5-2b
```

Ollama must be reachable from the backend. If the backend runs in a container, `localhost` points to that container; use an Ollama host address reachable from it instead. If OpenRouter is selected without an API key, the API runs in demo mode with deterministic opportunity data. Errors from a selected live provider return HTTP 502; the backend does not switch providers automatically.

## Run

```bash
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
