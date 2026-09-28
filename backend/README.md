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

CV storage uses a separate Ollama embedding model and a dedicated PGVector table. Configure these values in `backend/.env`:

```env
PGVECTOR_CONNECTION_STRING=postgresql+psycopg://user:password@localhost:5432/opportunity_radar
PGVECTOR_TABLE_NAME=cv_chunks
PGVECTOR_EMBEDDING_DIMENSION=768
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_EMBEDDING_BASE_URL=http://localhost:11434
```

The backend must be able to reach PostgreSQL and Ollama. Pull both configured models before uploading:

```bash
ollama pull <OLLAMA_MODEL>
ollama pull <OLLAMA_EMBEDDING_MODEL>
```

Enable the PGVector extension in the database before the first upload:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The backend creates and validates the configured vector table on upload. Its database role therefore needs permission to create tables in the selected schema. Set `PGVECTOR_EMBEDDING_DIMENSION` to the output dimension of the selected embedding model; a mismatch prevents writes.

## CV upload and data handling

`POST /api/chat` accepts an optional PDF in a multipart request, with a maximum size of 10 MiB. Text is extracted, split into page-aware chunks, embedded, and stored in PGVector. A successful response includes `cv_uploaded: true` and a `document_id`; the frontend treats a missing confirmation or a failed request as an upload failure. Malformed, encrypted, empty, or textless PDFs return HTTP 422, unsupported file types return HTTP 415, and unavailable storage or embeddings return HTTP 503.

Each successful upload replaces the previous active CV. The new chunks are written before old chunks are removed in the same database transaction, so a failed write preserves the prior CV. The original PDF file is not retained; extracted text chunks, filename, and page metadata are stored. The stored CV is not yet used to augment chat or retrieve RAG context.

This backend currently has no authentication or per-user data isolation. Every upload to the configured database replaces the same active CV, so this setup is single-user only and must not be exposed as a multi-user service. CV text and embeddings are sensitive personal data; restrict access to the database and its backups accordingly.

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Endpoints:

- `GET /health`
- `POST /api/chat`

The chat endpoint accepts JSON requests with `prompt` and `messages`, or multipart requests with those fields plus an optional PDF. PDF uploads are extracted and stored in PGVector before the response confirms success.

## Frontend connection

The Next.js app proxies browser requests through its own `/api/chat` route. Set this in `frontend/.env.local` when running the backend separately:

```env
BACKEND_URL=http://localhost:8000
```
