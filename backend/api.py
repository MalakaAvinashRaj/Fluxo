"""FastAPI backend for the autonomous agent system."""

import asyncio
import hashlib
import hmac
import os
import re
import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import structlog

from config import settings
from agent import AutonomousAgent
from services.session_manager import get_session_manager, SessionManager
from services.llm_service import get_llm_service
from services.flutter_preview_service import FlutterPreviewService
from tools import get_tool_registry
from errors.handlers import setup_error_handlers
from agent_logging.logger import setup_logging, RequestLogger
from agent_logging.metrics import start_metrics_server, metrics

logger = structlog.get_logger()
request_logger = RequestLogger()


# ─── IP helpers ───────────────────────────────────────────────────────────────

# Only honour forwarded-IP headers when we are actually running behind a trusted
# reverse proxy (Cloudflare / Nginx). Otherwise these headers are fully
# client-controlled and would let anyone forge a fresh identity per request to
# bypass per-IP quotas. Enable by setting TRUST_PROXY_HEADERS=1 in the
# environment for the proxied deployment only.
_TRUST_PROXY_HEADERS = os.environ.get("TRUST_PROXY_HEADERS", "").lower() in ("1", "true", "yes")

# Session IDs are UUID4; reject anything else early to keep them out of paths.
_SESSION_ID_RE = re.compile(r"^[0-9a-fA-F-]{8,64}$")


def _get_client_ip(request: Request) -> str:
    """Extract the client IP.

    Behind a trusted proxy we honour Cloudflare / forwarding headers; otherwise
    we use the direct peer address so the value cannot be spoofed.
    """
    if _TRUST_PROXY_HEADERS:
        for header in ("CF-Connecting-IP", "X-Forwarded-For", "X-Real-IP"):
            val = request.headers.get(header)
            if val:
                return val.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _quota_exceeded_response(detail: str) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": detail})


def _verify_session_owner(session, ip: str) -> None:
    """Ensure the requesting IP owns this session, else 404.

    We return 404 (not 403) so the existence of another user's session is not
    revealed. Sessions created before ownership tracking carry "unknown" and are
    treated as legacy-open to avoid locking users out after deploy.
    """
    owner = getattr(session, "creator_ip", "unknown")
    if owner not in ("unknown", ip):
        raise HTTPException(status_code=404, detail="Session not found")


# Request/Response models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    stream: bool = Field(default=True, description="Enable streaming response")
    autonomous: bool = Field(default=True, description="Enable autonomous tool execution")
    max_iterations: int = Field(default=10, ge=1, le=50, description="Maximum autonomous iterations")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    tool_calls: Optional[int] = None
    iterations: Optional[int] = None


class SessionCreateRequest(BaseModel):
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    session_id: str
    user_id: Optional[str]
    created_at: str
    phase: str = "idle"


class ToolsResponse(BaseModel):
    tools: list
    count: int


SESSION_TTL_DAYS = 7


async def _hourly_container_restart(preview_service: FlutterPreviewService):
    """Restart the Flutter build container every hour to free memory."""
    while True:
        await asyncio.sleep(3600)
        try:
            logger.info("Hourly container restart starting")
            await preview_service.start_build_container()
            logger.info("Hourly container restart complete")
        except Exception as e:
            logger.error("Hourly container restart failed", error=str(e))


async def _daily_session_cleanup(session_manager):
    """Delete sessions older than SESSION_TTL_DAYS every 24 hours."""
    from datetime import datetime, timezone
    while True:
        await asyncio.sleep(86400)
        try:
            sessions_path = Path(settings.session_storage_path)
            if not sessions_path.exists():
                continue
            cutoff = datetime.now(timezone.utc).timestamp() - SESSION_TTL_DAYS * 86400
            removed = 0
            # Only iterate session-metadata files (session_<id>.json), which carry
            # created_at. Skip the IP index/quota files and the memory files
            # (<id>.json) — the latter are removed alongside their metadata file.
            for f in sessions_path.glob("session_*.json"):
                try:
                    data = json.loads(f.read_text())
                    created_raw = data.get("created_at")
                    if not created_raw:
                        continue
                    created = datetime.fromisoformat(created_raw).timestamp()
                    if created < cutoff:
                        session_id = data.get("session_id") or f.stem[len("session_"):]
                        # Remove metadata file, paired memory file, and quota entry.
                        f.unlink(missing_ok=True)
                        (sessions_path / f"{session_id}.json").unlink(missing_ok=True)
                        creator_ip = data.get("creator_ip", "unknown")
                        await session_manager.remove_session_from_ip_index(session_id, creator_ip)
                        removed += 1
                except Exception:
                    pass
            logger.info("Daily session cleanup done", removed=removed)
        except Exception as e:
            logger.error("Daily session cleanup failed", error=str(e))


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""

    # Startup
    setup_logging()

    if settings.enable_metrics:
        start_metrics_server(settings.metrics_port)

    # Initialize components
    session_manager = get_session_manager()
    tool_registry = get_tool_registry()

    # Initialize Flutter build service and start container
    app.state.preview_service = FlutterPreviewService()
    await app.state.preview_service.start_build_container()

    # Start background maintenance tasks
    restart_task = asyncio.create_task(_hourly_container_restart(app.state.preview_service))
    cleanup_task = asyncio.create_task(_daily_session_cleanup(session_manager))

    logger.info(
        "Agent API started",
        host=settings.host,
        port=settings.port,
        websocket_port=settings.websocket_port,
        metrics_enabled=settings.enable_metrics,
        available_tools=len(tool_registry.list_tools())
    )

    yield

    restart_task.cancel()
    cleanup_task.cancel()

    # Shutdown — stop container and delete all local data
    await session_manager.shutdown()
    await app.state.preview_service.shutdown()

    logger.info("Agent API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Autonomous Agent API",
    description="Efficient AI agent system with parallel tool execution",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
_cors_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://fluxo.avinashrajmalaka.in",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup error handlers
setup_error_handlers(app)


# Dependency injection
def get_session_manager_dep() -> SessionManager:
    return get_session_manager()


# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    
    try:
        session_manager = get_session_manager()
        stats = await session_manager.get_session_statistics()
        
        tool_registry = get_tool_registry()
        tool_count = len(tool_registry.list_tools())
        
        return {
            "status": "healthy",
            "active_sessions": stats.get("active_sessions", 0),
            "available_tools": tool_count,
            "llm_service": settings.default_model
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/sessions", response_model=SessionResponse)
async def create_session(
    http_request: Request,
    request: SessionCreateRequest,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Create a new agent session."""

    ip = _get_client_ip(http_request)

    if not await session_manager.check_can_create_session(ip):
        logger.warning("Project quota hit", ip=ip)
        return _quota_exceeded_response(
            "You've reached the 4-project limit. Open an existing project to continue."
        )

    try:
        session = await session_manager.create_session(
            user_id=request.user_id,
            metadata=request.metadata
        )
        session.creator_ip = ip
        await session_manager.record_session_for_ip(session.session_id, ip)
        await session_manager._persist_session(session)

        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at.isoformat(),
            phase=session.phase,
        )
        
    except Exception as e:
        logger.error("Failed to create session", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create session")


@app.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    http_request: Request,
    background_tasks: BackgroundTasks,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Get session information including conversation history."""

    session = await session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    _verify_session_owner(session, _get_client_ip(http_request))

    # If the container project is gone (e.g. after restart) but we have saved
    # source files, silently restore it in the background for future builds.
    if session.build_count > 0 and session_id not in app.state.preview_service.initialized_projects:
        background_tasks.add_task(app.state.preview_service.restore_project, session_id)

    history = await session.memory.get_conversation_history(max_messages=100)
    # Only include user/assistant turns (skip system messages)
    messages = [
        {"role": m["role"], "content": m.get("content", "")}
        for m in history
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]

    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "is_active": session.is_active,
        "phase": session.phase,
        "message_count": session.message_count,
        "messages": messages,
    }


@app.get("/my-sessions")
async def my_sessions(
    http_request: Request,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Return all sessions and quota info for the requesting IP."""
    ip = _get_client_ip(http_request)
    sessions_data = session_manager.get_sessions_for_ip(ip)
    quota = session_manager.get_ip_quota(ip)

    output_dir = app.state.preview_service.output_dir
    sessions_out = []
    for s in sessions_data:
        session_id = s.get("session_id", "")
        build_path = output_dir / session_id / "build" / "web"
        has_build = build_path.exists()
        sessions_out.append({
            "session_id": session_id,
            "created_at": s.get("created_at", ""),
            "last_active": s.get("last_activity", ""),
            "phase": s.get("phase", "idle"),
            "message_count": quota["messages_by_session"].get(session_id, 0),
            "has_build": has_build,
            "preview_url": f"/preview/{session_id}/" if has_build else None,
        })

    return {
        "sessions": sessions_out,
        "quota": {
            "projects_used": quota["projects_used"],
            "projects_remaining": quota["projects_remaining"],
            "messages_limit": quota["messages_limit"],
        },
    }


@app.delete("/sessions/{session_id}")
async def end_session(
    session_id: str,
    http_request: Request,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """End a session."""

    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _verify_session_owner(session, _get_client_ip(http_request))

    success = await session_manager.end_session(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session ended successfully"}


@app.post("/sessions/{session_id}/chat")
async def chat(
    session_id: str,
    http_request: Request,
    request: ChatRequest,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Chat with the agent (non-streaming)."""

    ip = _get_client_ip(http_request)

    session = await session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    _verify_session_owner(session, ip)

    if not await session_manager.check_can_send_message(session_id, ip):
        return _quota_exceeded_response(
            "This project has reached the 20-message limit."
        )

    # Record message and bump counter before processing
    await session_manager.increment_ip_message_count(session_id, ip)

    agent = AutonomousAgent(session, preview_service=app.state.preview_service)

    # Collect all responses
    full_response = ""
    tool_calls_count = 0
    iterations = 0
    
    async for chunk in agent.chat(
        user_message=request.message,
        stream=False,
        autonomous=request.autonomous,
        max_iterations=request.max_iterations
    ):
        if chunk["type"] == "content":
            full_response += chunk["data"]
        elif chunk["type"] == "tools_complete":
            tool_calls_count += chunk["data"]["total"]
        elif chunk["type"] == "done":
            iterations = chunk["data"]["iterations"]
    
    return ChatResponse(
        session_id=session_id,
        response=full_response,
        tool_calls=tool_calls_count if tool_calls_count > 0 else None,
        iterations=iterations if iterations > 1 else None
    )


@app.post("/sessions/{session_id}/chat/stream")
async def chat_stream(
    session_id: str,
    http_request: Request,
    request: ChatRequest,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Chat with the agent (streaming)."""

    ip = _get_client_ip(http_request)

    session = await session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    _verify_session_owner(session, ip)

    if not await session_manager.check_can_send_message(session_id, ip):
        return _quota_exceeded_response(
            "This project has reached the 20-message limit."
        )

    # Record message and bump counter before processing
    await session_manager.increment_ip_message_count(session_id, ip)

    agent = AutonomousAgent(session, preview_service=app.state.preview_service)

    async def generate_response():
        async for chunk in agent.chat(
            user_message=request.message,
            stream=request.stream,
            autonomous=request.autonomous,
            max_iterations=request.max_iterations
        ):
            yield f"data: {json.dumps(chunk)}\n\n"

        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/stream-event",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/tools", response_model=ToolsResponse)
async def get_tools():
    """Get available tools."""
    
    tool_registry = get_tool_registry()
    tools = []
    
    for tool_name in tool_registry.list_tools():
        tool = tool_registry.get_tool(tool_name)
        if tool:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "schema": tool.schema.to_openai_format(),
                "statistics": tool.get_statistics()
            })
    
    return ToolsResponse(tools=tools, count=len(tools))


@app.get("/sessions/{session_id}/context")
async def get_context(
    session_id: str,
    http_request: Request,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Get conversation context for a session."""

    session = await session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    _verify_session_owner(session, _get_client_ip(http_request))

    agent = AutonomousAgent(session, preview_service=app.state.preview_service)

    try:
        context = await agent.get_context_summary()
        conversation = await session.memory.get_conversation_history(max_messages=50)
        
        return {
            "context": context,
            "recent_messages": conversation
        }
        
    except Exception as e:
        logger.error("Failed to get context", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get context")


@app.delete("/sessions/{session_id}/context")
async def clear_context(
    session_id: str,
    http_request: Request,
    keep_system: bool = True,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Clear conversation context for a session."""

    session = await session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    _verify_session_owner(session, _get_client_ip(http_request))

    agent = AutonomousAgent(session, preview_service=app.state.preview_service)

    success = await agent.clear_context(keep_system_messages=keep_system)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear context")
    
    return {"message": "Context cleared successfully"}


@app.get("/stats")
async def get_statistics(
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Get system statistics."""
    
    try:
        session_stats = await session_manager.get_session_statistics()
        
        tool_registry = get_tool_registry()
        tool_stats = tool_registry.get_tool_statistics()
        
        return {
            "sessions": session_stats,
            "tools": tool_stats,
            "system": {
                "available_tools": len(tool_registry.list_tools()),
                "llm_service": settings.default_model,
                "max_parallel_tools": settings.max_parallel_tools
            }
        }
        
    except Exception as e:
        logger.error("Failed to get statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get statistics")


# Flutter Warmup Endpoint
@app.get("/sessions/{session_id}/warmup")
async def warmup_session(
    session_id: str,
    http_request: Request,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Start Flutter container warmup and stream phase events via SSE."""

    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    _verify_session_owner(session, _get_client_ip(http_request))

    preview_service: FlutterPreviewService = app.state.preview_service

    async def generate_events():
        async for event in preview_service.warmup_session(session_id):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/sessions/{session_id}/pin")
async def pin_session(
    session_id: str,
    http_request: Request,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Pin a session so its data survives server shutdown."""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _verify_session_owner(session, _get_client_ip(http_request))
    app.state.preview_service.pin_session(session_id)
    return {"success": True, "pinned": True}


@app.delete("/sessions/{session_id}/pin")
async def unpin_session(
    session_id: str,
    http_request: Request,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Unpin a session — it will be cleaned up on next shutdown."""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _verify_session_owner(session, _get_client_ip(http_request))
    app.state.preview_service.unpin_session(session_id)
    return {"success": True, "pinned": False}


@app.delete("/sessions/{session_id}/full")
async def delete_session_full(
    session_id: str,
    http_request: Request,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Fully delete a session and all its data (Docker + host + session storage)."""
    ip = _get_client_ip(http_request)
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _verify_session_owner(session, ip)

    creator_ip = getattr(session, "creator_ip", "unknown")
    await session_manager.end_session(session_id)
    # Free the IP's project-quota slot so deletion actually reclaims capacity.
    await session_manager.remove_session_from_ip_index(session_id, creator_ip)
    success = await app.state.preview_service.delete_session(session_id)
    return {"success": success}


@app.post("/sessions/{session_id}/rebuild")
async def rebuild_preview(
    session_id: str,
    http_request: Request,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Re-run flutter build web for an existing session without uploading new files."""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    _verify_session_owner(session, _get_client_ip(http_request))

    preview_service: FlutterPreviewService = app.state.preview_service
    result = await preview_service.rebuild_project(session_id)
    return result


# Serve Flutter build output as static files
@app.get("/preview/{session_id}/{path:path}")
async def serve_preview(session_id: str, path: str = ""):
    """Serve the static Flutter web build for a session."""
    # Guard against path traversal: the resolved target must stay inside the
    # session's build directory. session_id is also constrained to a UUID shape
    # so it can't be used to climb out via "..".
    if not _SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=404, detail="Preview not found")

    build_dir = (Path("./flutter_output") / session_id / "build" / "web").resolve()
    file_path = (build_dir / (path if path else "index.html")).resolve()

    if not (file_path == build_dir or build_dir in file_path.parents):
        raise HTTPException(status_code=404, detail="Preview not found")

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Preview not ready — build may still be in progress")

    return FileResponse(file_path)


# WebSocket endpoint for real-time communication
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """WebSocket endpoint for real-time agent communication."""
    
    await websocket.accept()

    # Resolve the client IP for quota + ownership, mirroring the HTTP path.
    ws_ip = "unknown"
    if _TRUST_PROXY_HEADERS:
        for header in ("cf-connecting-ip", "x-forwarded-for", "x-real-ip"):
            val = websocket.headers.get(header)
            if val:
                ws_ip = val.split(",")[0].strip()
                break
    if ws_ip == "unknown" and websocket.client:
        ws_ip = websocket.client.host

    try:
        # Get or create session
        session = await session_manager.get_session(session_id)

        if not session:
            # New session: enforce the per-IP project cap and record ownership.
            if not await session_manager.check_can_create_session(ws_ip):
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"error": "Project limit reached"}
                }))
                await websocket.close()
                return
            session = await session_manager.create_session()
            session.creator_ip = ws_ip
            await session_manager.record_session_for_ip(session.session_id, ws_ip)
            await session_manager._persist_session(session)
        else:
            # Existing session must belong to the connecting IP.
            owner = getattr(session, "creator_ip", "unknown")
            if owner not in ("unknown", ws_ip):
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"error": "Session not found"}
                }))
                await websocket.close()
                return

        agent = AutonomousAgent(session, preview_service=app.state.preview_service)
        
        logger.info(
            "WebSocket connection established",
            session_id=session.session_id,
            client=websocket.client
        )
        
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                message_type = message_data.get("type")
                
                if message_type == "chat":
                    # Enforce the per-session message cap before processing.
                    if not await session_manager.check_can_send_message(session.session_id, ws_ip):
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "data": {"error": "This project has reached the 20-message limit."}
                        }))
                        continue
                    await session_manager.increment_ip_message_count(session.session_id, ws_ip)

                    # Process chat message
                    user_message = message_data.get("message", "")
                    autonomous = message_data.get("autonomous", True)
                    max_iterations = message_data.get("max_iterations", 10)

                    # Stream response back to client
                    async for chunk in agent.chat(
                        user_message=user_message,
                        stream=True,
                        autonomous=autonomous,
                        max_iterations=max_iterations
                    ):
                        await websocket.send_text(json.dumps(chunk))
                
                elif message_type == "get_context":
                    # Send context information
                    context = await agent.get_context_summary()
                    await websocket.send_text(json.dumps({
                        "type": "context",
                        "data": context
                    }))
                
                elif message_type == "clear_context":
                    # Clear conversation context
                    success = await agent.clear_context(
                        keep_system_messages=message_data.get("keep_system", True)
                    )
                    await websocket.send_text(json.dumps({
                        "type": "context_cleared",
                        "data": {"success": success}
                    }))
                
                else:
                    # Unknown message type
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {"error": f"Unknown message type: {message_type}"}
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"error": "Invalid JSON message"}
                }))
            
            except Exception as e:
                logger.error(
                    "Error processing WebSocket message",
                    session_id=session.session_id,
                    error=str(e),
                    exc_info=True
                )
                
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"error": "Internal error processing message"}
                }))

    except WebSocketDisconnect:
        logger.info(
            "WebSocket connection closed",
            session_id=session_id
        )
    
    except Exception as e:
        logger.error(
            "WebSocket connection error",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )


_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
_REPO_ROOT = Path(__file__).parent.parent


async def _run_deploy():
    """Pull latest code, rebuild frontend, restart service."""
    try:
        logger.info("Webhook deploy started")
        proc = await asyncio.create_subprocess_exec(
            "bash", str(_REPO_ROOT / "deploy" / "deploy.sh"),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(_REPO_ROOT),
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            logger.info("Webhook deploy succeeded")
        else:
            logger.error("Webhook deploy failed", output=stdout.decode())
    except Exception as e:
        logger.error("Webhook deploy error", error=str(e))


@app.post("/webhook/github")
async def github_webhook(http_request: Request, background_tasks: BackgroundTasks):
    """Receive GitHub push events and trigger an auto-deploy."""
    body = await http_request.body()

    # Fail closed: without a configured secret we cannot authenticate the sender,
    # so refuse rather than allowing anyone to trigger a deploy.
    if not _WEBHOOK_SECRET:
        logger.error("Webhook rejected: GITHUB_WEBHOOK_SECRET is not configured")
        raise HTTPException(status_code=503, detail="Webhook not configured")

    # Verify signature
    sig_header = http_request.headers.get("X-Hub-Signature-256", "")
    mac = hmac.new(_WEBHOOK_SECRET.encode(), body, hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    if not hmac.compare_digest(sig_header, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = http_request.headers.get("X-GitHub-Event", "")
    if event == "push":
        background_tasks.add_task(_run_deploy)
        logger.info("Deploy triggered by GitHub push")

    return {"ok": True}


# Serve React frontend — must be last so API routes take priority
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_config=None  # Use our structured logging
    )