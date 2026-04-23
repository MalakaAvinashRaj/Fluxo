# Fluxo

An AI-powered Flutter app builder. Describe what you want, the agent plans it out, then writes, builds, and serves a live Flutter web app — rendered in a phone preview inside the browser.

## How it works

1. User opens the workspace and types a prompt
2. The agent runs a **planning phase** — classifies complexity, summarises the build plan, and asks clarifying questions if needed
3. Once the plan is confirmed, the Python agent writes Flutter code into a persistent Docker container
4. The container runs `flutter build web`; the output is copied back to the host and served as static files
5. The built app renders in an iframe phone preview — live in the browser
6. The user iterates via chat (up to 20 messages per project)

No account or login needed — access is IP-based.

## Stack

- **Frontend** — React 19, TypeScript, Vite, Tailwind CSS
- **Backend** — Python, FastAPI, autonomous agent with tool execution loop
- **AI** — OpenAI (GPT-4o / GPT-4o-mini), RAG over Flutter docs via ChromaDB
- **Build layer** — Single persistent Docker container running Flutter SDK (shared across all sessions)
- **Infra** — Cloudflare Tunnel for public HTTPS access (TLS terminated by Cloudflare)

## Project structure

```
fluxo/
├── frontend/          React UI (chat, code editor, file explorer, phone preview)
├── backend/           Python FastAPI backend + autonomous agent
│   ├── agent.py       Core agent loop — planning phase + tool selection + execution
│   ├── api.py         REST endpoints + IP quota enforcement
│   ├── config.py      Environment-based configuration (pydantic-settings)
│   ├── services/      Session manager, LLM service, RAG, Flutter preview, task executor
│   ├── tools/         File ops, shell commands, tool registry
│   ├── errors/        Error handling and recovery
│   └── agent_logging/ Structured logging and metrics
└── Dockerfile         Flutter SDK build container image
```

## Local development

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY
python main.py         # starts on :8081
```

**Frontend**
```bash
cd frontend
npm install
npm run dev            # starts on :5173, proxies API to :8081
```

**Flutter build container** (required for preview to work)
```bash
docker build -t flutter-dev-server:latest .
```

## Production deployment (home Linux server)

The backend serves everything — API, Flutter previews, and the built React frontend — on a single port. No Nginx required.

```bash
# 1. Build the Flutter container image (once, or on Dockerfile changes)
docker build -t flutter-dev-server:latest .

# 2. Build the React frontend
cd frontend && npm install && npm run build && cd ..

# 3. Configure environment
cp backend/.env.example /opt/fluxo/.env
# Edit /opt/fluxo/.env — set OPENAI_API_KEY, AGENT_PORT=8081, etc.

# 4. Install and start the systemd service
sudo cp deploy/fluxo-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now fluxo-backend

# 5. Point Cloudflare Tunnel to port 8081
# In /etc/cloudflared/config.yml, set:
#   service: http://localhost:8081
# Then: sudo systemctl restart cloudflared
```

For redeployment after code changes:
```bash
./deploy.sh
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/sessions` | Create a new session |
| `GET` | `/sessions/{id}` | Get session info and chat history |
| `POST` | `/sessions/{id}/chat/stream` | Stream AI agent response (SSE) |
| `GET` | `/sessions/{id}/warmup` | Warm up the Flutter project in the container (SSE) |
| `POST` | `/sessions/{id}/rebuild` | Rebuild the Flutter app |
| `GET` | `/preview/{id}/{path}` | Serve Flutter web build output (static files) |
| `GET` | `/my-sessions` | List previous sessions for the current IP |
| `GET` | `/health` | Health check |
| `GET` | `/stats` | Usage stats |

## Usage limits

| Limit | Value |
|-------|-------|
| Projects per IP | 4 (hard cap, no reset) |
| Messages per project | 20 (hard cap) |

No login required. Limits are tracked per IP and persist across server restarts.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Required |
| `AGENT_HOST` | `0.0.0.0` | Backend bind host |
| `AGENT_PORT` | `8081` | Backend listen port |
| `DEFAULT_MODEL` | `gpt-4o-mini` | OpenAI model |
| `MAX_TOKENS` | `128000` | Max context tokens |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `console` | `console` or `json` |
| `SESSION_STORAGE_PATH` | `./sessions` | Where session JSON files are stored |
| `FLUTTER_OUTPUT_DIR` | `./flutter_output` | Where build outputs are stored on host |
