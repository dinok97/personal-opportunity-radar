# Personal Opportunity Radar Documentation

## Run Locally

Start the backend and frontend in separate terminal.

### 1. Start the backend

From the repository root:

```bash
cd backend
source .venv/bin/activate
pip install -e ".[test]"
```

Before starting the backend, copy the environment template and fill the value accordingly:

```bash
cp .env.example .env
```

Finally, run the backend by command:

```bash
uvicorn app.main:app --reload --port 8000
```

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