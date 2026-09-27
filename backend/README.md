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

CV vector storage is configured separately from chat. Set `PGVECTOR_CONNECTION_STRING` to a PostgreSQL connection string for a database with the `vector` extension available, and configure `PGVECTOR_TABLE_NAME` and `PGVECTOR_EMBEDDING_DIMENSION` to match the selected embedding model. The default embedding model is `nomic-embed-text`; pull it with `ollama pull nomic-embed-text`. The backend must be able to reach both PostgreSQL and the Ollama embedding endpoint (`OLLAMA_EMBEDDING_BASE_URL`). These settings and dependencies prepare the backend for CV storage; upload extraction and vector persistence are not enabled by this setup change alone.

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Endpoints:

- `GET /health`
- `POST /api/chat`

The chat endpoint accepts JSON requests with `prompt` and `messages`, or multipart requests with those fields plus an optional PDF. PDF text extraction is intentionally not enabled yet; the current upload boundary only validates and receives the file.

## Frontend connection

The Next.js app proxies browser requests through its own `/api/chat` route. Set this in `frontend/.env.local` when running the backend separately:

```env
BACKEND_URL=http://localhost:8000
```
