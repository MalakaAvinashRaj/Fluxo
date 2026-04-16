# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Plan & Review

### Before starting work
- Always in plan mode to make a plan.
- After get the plan, make sure you write the plan to .claude/tasks/TASK_NAME.md
- The plan should be a detailed implementation plan and the reasoning behind them, as well as tasks broken down.
- if the task require externa knowledge or certain package, also research to get latest knowledge (use task tool for research)
- Don't over plan it, always think MVP.
- Once you write the plan firstly ask me to review it. DO not continue until i approve the plan.

### While Implementing
- You should update the plan as you work.
- After you complete the tasks in the plan, you should update and append detailed descriptions of the changes you made, so following tasks can be forworder to other engineers.

## Repository Structure

This is a production-ready Python AI Agent platform with React frontend and autonomous backend:

- **backend/**: Python autonomous agent backend with tool execution, session management, and AI integration
- **frontend/**: Vite React frontend with modern workspace interface for AI development

## Common Commands

### Python Backend
```bash
cd backend
pip install -r requirements.txt  # Install Python dependencies
python main.py                   # Start Python agent backend on port 8080
```

### React Frontend
```bash
cd frontend
npm install       # Install dependencies
npm run dev       # Development server with Vite
npm run build     # Production build (TypeScript + Vite)
npm run lint      # ESLint check
npm run preview   # Preview production build
```

## Architecture Overview

### System Flow
The platform follows a clean client-server architecture with AI integration:
- **React Frontend** → **Python Backend** → **Docker Containers** (when needed)
- Real-time AI chat interface with autonomous code generation
- Production-ready error handling, logging, and monitoring

### Frontend Architecture (React)
- **Framework**: Vite + React 19 + TypeScript
- **Routing**: React Router DOM for navigation (HomePage, WorkspacePage)
- **Components**: Modern workspace components (ChatPanel, CodeEditor, FileExplorer, PhonePreview)
- **Styling**: Tailwind CSS with clean, minimal Lovable.dev-inspired design
- **Services**: Production-grade API service layer with retry logic and error boundaries
- **State Management**: Custom hooks for API state management

### Backend Architecture (Python)
- **Runtime**: Python with FastAPI server architecture
- **Port**: 8080 for main API endpoints
- **AI Integration**: Autonomous agent with tool execution capabilities
- **Session Management**: UUID-based sessions with persistence
- **Error Handling**: Comprehensive logging and error recovery
- **Docker Integration**: Spawns containers for isolated development environments

### Key Service Classes
**Frontend Services:**
- `ApiService`: Production HTTP client with retry logic and error handling
- `Logger`: Context-aware logging with development/production modes
- `ErrorBoundary`: React error boundary for graceful error handling

**Backend Services:**
- `Agent`: Core autonomous AI agent with tool execution
- `SessionManager`: UUID-based session management and persistence
- `TaskExecutor`: Handles tool execution (file ops, commands, search)
- `LLMService`: OpenAI integration with enhanced prompting
- `AgentLogging`: Structured logging with metrics and monitoring

### API Endpoints
- `POST /sessions` - Create new session
- `GET /sessions/{id}` - Get session information
- `POST /sessions/{id}/chat/stream` - Stream response from AI agent
- `GET /sessions/{id}/warmup` - Warm up Flutter container (SSE)
- `POST /sessions/{id}/rebuild` - Rebuild Flutter app
- `GET /preview/{id}/{path}` - Serve Flutter web build output
- `GET /health` - Health check endpoint for monitoring

### AI Agent Workflow
The autonomous Python agent handles complex development tasks:
1. **Request Analysis**: Processes natural language requests from users
2. **Tool Selection**: Chooses appropriate tools (file ops, search, commands)
3. **Autonomous Execution**: Executes tasks independently with error recovery
4. **Code Generation**: Creates files, applications, and complete projects
5. **Session Persistence**: Maintains conversation history and context

### File Organization
**Frontend (`frontend/`):**
- `src/pages/` - HomePage, WorkspacePage
- `src/components/` - UI components and workspace components
- `src/services/` - API service layer with production error handling
- `src/config/` - Environment configuration and validation
- `src/hooks/` - Custom React hooks for API state management
- `src/utils/` - Logger and utility functions

**Backend (`backend/`):**
- `main.py` - Main server entry point
- `agent.py` - Core autonomous AI agent
- `api.py` - API endpoints and routing
- `services/` - Session management, LLM service, task executor
- `tools/` - File operations, search, command execution
- `errors/` - Error handling and recovery systems

### Development Workflow
1. **Frontend Connection**: React frontend connects to Python backend (port 8080)
2. **Session Creation**: Backend creates UUID-based session for user
3. **AI Chat Interface**: User submits natural language requests via chat
4. **Autonomous Processing**: Python agent analyzes request and selects tools
5. **Code Generation**: Agent creates files, writes code, executes commands
6. **Real-time Updates**: Frontend displays AI responses and generated content
7. **Session Persistence**: All interactions saved for context and history

### Docker Integration
- **Purpose**: Isolated development environments for user-generated projects
- **Usage**: Python backend spawns Docker containers when needed
- **Container Type**: Flutter build containers (flutter web build)
- **Management**: Automatic lifecycle management with cleanup

## Production Features

### Frontend Production Features
- ✅ **Error Boundaries**: Comprehensive React error handling with graceful fallbacks
- ✅ **Production Logging**: Context-aware logging (development vs production modes)
- ✅ **API Service Layer**: Centralized HTTP client with automatic retry logic
- ✅ **Environment Validation**: Startup environment variable validation
- ✅ **Health Checks**: Built-in connection monitoring and health endpoints
- ✅ **Loading States**: Proper loading indicators with real-time status updates
- ✅ **Connection Retry**: Automatic backend connection retry with user feedback
- ✅ **IP Rate Limiting**: 5 sessions / 25 messages per IP per hour

### Backend Production Features
- ✅ **Session Management**: UUID-based sessions with file persistence
- ✅ **Tool Execution**: File operations, search, and command execution capabilities
- ✅ **Error Recovery**: Graceful error handling with detailed logging
- ✅ **Structured Logging**: Production-ready logging with context and metrics
- ✅ **Health Endpoints**: Service health monitoring for deployment
- ✅ **Autonomous Agent**: Independent task execution with tool selection
- ✅ **RAG Knowledge Base**: ChromaDB-backed Flutter documentation retrieval

### Development vs Production
- **Development**: Human-readable console logs, detailed error messages
- **Production**: Structured JSON logs, sanitized error responses
- **Environment**: Configurable via environment variables
- **Monitoring**: Health checks and status endpoints for deployment
