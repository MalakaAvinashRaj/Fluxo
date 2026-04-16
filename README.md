# Fluxo

Fluxo is an AI-powered Flutter app builder. Describe what you want and it generates a complete, runnable Flutter app — live in a phone preview inside the browser.

## How it works

1. User types a prompt in the chat (e.g. "build me a todo app")
2. The Python agent writes Flutter code, copies it into a persistent Docker container, and runs `flutter build web`
3. The built output is served back through the backend and rendered in an iframe phone preview
4. The user can iterate — chat to make changes, hit Rebuild, or view the generated code

## Stack

- **Frontend** — React 19, TypeScript, Vite, Tailwind CSS
- **Backend** — Python, FastAPI, OpenAI API
- **Agent** — Autonomous tool-calling loop with RAG (ChromaDB + Flutter docs)
- **Build layer** — Persistent Docker container running Flutter SDK
- **Infra** — Nginx reverse proxy, Cloudflare Tunnel for home-server deployment

## Project structure

```
fluxo/
├── frontend/          React + TypeScript UI
├── backend/           Python FastAPI agent
├── nginx/             Nginx reverse proxy config
├── Dockerfile         Flutter build container image
└── docker-compose.yml Production orchestration
```

## Local development

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY
python main.py         # starts on :8080
```

**Frontend**
```bash
cd frontend
npm install
npm run dev            # starts on :5173
```

The frontend talks to the backend at `http://localhost:8080` by default.

## Production (Docker Compose)

```bash
# Build the Flutter container image first
docker build -t flutter-dev-server:latest .

# Build the React app
cd frontend && npm install && npm run build && cd ..

# Add your key
echo "OPENAI_API_KEY=sk-..." > backend/.env

# Start
docker compose up -d
```

Nginx serves the React build at `/` and proxies all API and preview traffic to the backend.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Required |
| `AGENT_PORT` | `8080` | Backend listen port |
| `DEFAULT_MODEL` | `gpt-4o-mini` | OpenAI model |
| `PREVIEW_BASE_URL` | `http://localhost:8080` | Set to `""` in prod (relative URLs via Nginx) |
| `VITE_API_BASE_URL` | `http://localhost:8080` | Set to `""` in prod build |
