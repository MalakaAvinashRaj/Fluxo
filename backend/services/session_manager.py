"""Session management for the autonomous agent system."""

import uuid
import json
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import structlog

from config import settings
from memory import MemoryManager
from errors.exceptions import SessionError
from agent_logging.metrics import metrics

logger = structlog.get_logger()


class Session:
    """Represents an agent session."""
    
    def __init__(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.is_active = True

        # Planning phase: "idle" → "planning" → "building"
        self.phase = "idle"

        # IP that created this session
        self.creator_ip: str = "unknown"

        # Initialize memory manager
        self.memory = MemoryManager(session_id)

        # Session statistics
        self.message_count = 0
        self.tool_calls_count = 0
        self.error_count = 0
        self.build_count = 0
        
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def increment_message_count(self):
        """Increment message count."""
        self.message_count += 1
        self.update_activity()
    
    def increment_tool_calls(self):
        """Increment tool calls count."""
        self.tool_calls_count += 1
        self.update_activity()
    
    def increment_error_count(self):
        """Increment error count."""
        self.error_count += 1
        self.update_activity()
    
    def get_duration_minutes(self) -> float:
        """Get session duration in minutes."""
        duration = datetime.utcnow() - self.created_at
        return duration.total_seconds() / 60
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_active": self.is_active,
            "phase": self.phase,
            "creator_ip": self.creator_ip,
            "message_count": self.message_count,
            "tool_calls_count": self.tool_calls_count,
            "error_count": self.error_count,
            "build_count": self.build_count,
            "duration_minutes": self.get_duration_minutes()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create session from dictionary."""
        session = cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {})
        )
        
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.last_activity = datetime.fromisoformat(data["last_activity"])
        session.is_active = data.get("is_active", True)
        session.phase = data.get("phase", "idle")
        session.creator_ip = data.get("creator_ip", "unknown")
        session.message_count = data.get("message_count", 0)
        session.tool_calls_count = data.get("tool_calls_count", 0)
        session.error_count = data.get("error_count", 0)
        session.build_count = data.get("build_count", 0)
        
        return session


class SessionManager:
    """Manages agent sessions with persistence and cleanup."""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or settings.session_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory session cache
        self._sessions: Dict[str, Session] = {}
        
        # Session cleanup settings
        self.session_timeout_hours = 24
        self.cleanup_interval_minutes = 30
        
        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    # ── Quota limits ──────────────────────────────────────────────────────────
    MAX_PROJECTS_PER_IP = 4
    MAX_MESSAGES_PER_SESSION = 20

    # ── IP index + quota helpers ──────────────────────────────────────────────

    def _ip_index_path(self) -> Path:
        return self.storage_path / "ip_index.json"

    def _ip_quotas_path(self) -> Path:
        return self.storage_path / "ip_quotas.json"

    def _load_ip_index(self) -> Dict[str, List[str]]:
        p = self._ip_index_path()
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
        return {}

    def _save_ip_index(self, index: Dict[str, List[str]]) -> None:
        self._ip_index_path().write_text(json.dumps(index, indent=2))

    def _load_ip_quotas(self) -> Dict[str, Any]:
        p = self._ip_quotas_path()
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
        return {}

    def _save_ip_quotas(self, quotas: Dict[str, Any]) -> None:
        self._ip_quotas_path().write_text(json.dumps(quotas, indent=2))

    def get_ip_quota(self, ip: str) -> Dict[str, Any]:
        """Return quota info for an IP: projects used, messages by session."""
        quotas = self._load_ip_quotas()
        entry = quotas.get(ip, {"projects": 0, "messages_by_session": {}})
        return {
            "projects_used": entry.get("projects", 0),
            "projects_remaining": max(0, self.MAX_PROJECTS_PER_IP - entry.get("projects", 0)),
            "messages_by_session": entry.get("messages_by_session", {}),
            "messages_limit": self.MAX_MESSAGES_PER_SESSION,
        }

    def check_can_create_session(self, ip: str) -> bool:
        """True if IP is under the 4-project hard cap."""
        quota = self.get_ip_quota(ip)
        return quota["projects_used"] < self.MAX_PROJECTS_PER_IP

    def check_can_send_message(self, session_id: str, ip: str) -> bool:
        """True if this session is under the 20-message hard cap."""
        quota = self.get_ip_quota(ip)
        used = quota["messages_by_session"].get(session_id, 0)
        return used < self.MAX_MESSAGES_PER_SESSION

    def record_session_for_ip(self, session_id: str, ip: str) -> None:
        """Register a new session under an IP in both index and quotas files."""
        # Update index
        index = self._load_ip_index()
        index.setdefault(ip, [])
        if session_id not in index[ip]:
            index[ip].append(session_id)
        self._save_ip_index(index)

        # Update quotas
        quotas = self._load_ip_quotas()
        entry = quotas.setdefault(ip, {"projects": 0, "messages_by_session": {}})
        entry["projects"] = len(index[ip])
        entry["messages_by_session"].setdefault(session_id, 0)
        self._save_ip_quotas(quotas)

    def increment_ip_message_count(self, session_id: str, ip: str) -> int:
        """Bump message counter for this session. Returns new count."""
        quotas = self._load_ip_quotas()
        entry = quotas.setdefault(ip, {"projects": 0, "messages_by_session": {}})
        entry["messages_by_session"].setdefault(session_id, 0)
        entry["messages_by_session"][session_id] += 1
        self._save_ip_quotas(quotas)
        return entry["messages_by_session"][session_id]

    def get_sessions_for_ip(self, ip: str) -> List[Dict[str, Any]]:
        """Return metadata for all sessions created by this IP."""
        index = self._load_ip_index()
        session_ids = index.get(ip, [])
        result = []
        for sid in session_ids:
            session_file = self.storage_path / f"session_{sid}.json"
            if session_file.exists():
                try:
                    data = json.loads(session_file.read_text())
                    result.append(data)
                except Exception:
                    pass
        result.sort(key=lambda s: s.get("last_activity", ""), reverse=True)
        return result

    def remove_session_from_ip_index(self, session_id: str, ip: str) -> None:
        """Remove a deleted session from the IP index and update quota count."""
        index = self._load_ip_index()
        if ip in index:
            index[ip] = [s for s in index[ip] if s != session_id]
            if not index[ip]:
                del index[ip]
        self._save_ip_index(index)

        quotas = self._load_ip_quotas()
        if ip in quotas:
            quotas[ip]["projects"] = len(index.get(ip, []))
            quotas[ip]["messages_by_session"].pop(session_id, None)
        self._save_ip_quotas(quotas)

    # ── Session lifecycle ─────────────────────────────────────────────────────

    async def create_session(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Create a new session."""
        
        try:
            session_id = str(uuid.uuid4())
            
            session = Session(
                session_id=session_id,
                user_id=user_id,
                metadata=metadata
            )
            
            # Load existing memory if available
            await session.memory.load_session()
            
            # Store in cache
            self._sessions[session_id] = session
            
            # Persist session
            await self._persist_session(session)
            
            # Update metrics
            metrics.update_active_sessions(len(self._sessions))
            
            logger.info(
                "Session created",
                session_id=session_id,
                user_id=user_id,
                total_sessions=len(self._sessions)
            )
            
            return session
            
        except Exception as e:
            logger.error(
                "Failed to create session",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            raise SessionError(
                f"Failed to create session: {e}",
                operation="create_session"
            )
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        
        try:
            # Check cache first
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.update_activity()
                return session
            
            # Try to load from storage
            session = await self._load_session(session_id)
            if session:
                # Add to cache
                self._sessions[session_id] = session
                session.update_activity()
                
                logger.debug(
                    "Session loaded from storage",
                    session_id=session_id
                )
                
                return session
            
            logger.warning(
                "Session not found",
                session_id=session_id
            )
            
            return None
            
        except Exception as e:
            logger.error(
                "Failed to get session",
                session_id=session_id,
                error=str(e),
                exc_info=True
            )
            raise SessionError(
                f"Failed to get session: {e}",
                session_id=session_id,
                operation="get_session"
            )
    
    async def end_session(self, session_id: str) -> bool:
        """End a session."""
        
        try:
            session = self._sessions.get(session_id)
            
            if not session:
                logger.warning(
                    "Attempted to end non-existent session",
                    session_id=session_id
                )
                return False
            
            # Mark as inactive
            session.is_active = False
            session.update_activity()
            
            # Persist final state
            await self._persist_session(session)
            
            # Remove from cache
            del self._sessions[session_id]
            
            # Update metrics
            metrics.update_active_sessions(len(self._sessions))
            
            logger.info(
                "Session ended",
                session_id=session_id,
                duration_minutes=session.get_duration_minutes(),
                message_count=session.message_count,
                tool_calls=session.tool_calls_count,
                errors=session.error_count
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to end session",
                session_id=session_id,
                error=str(e),
                exc_info=True
            )
            raise SessionError(
                f"Failed to end session: {e}",
                session_id=session_id,
                operation="end_session"
            )
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[Session]:
        """List sessions with optional filtering."""
        
        try:
            sessions = []
            
            # Get sessions from cache
            for session in self._sessions.values():
                if user_id and session.user_id != user_id:
                    continue
                
                if active_only and not session.is_active:
                    continue
                
                sessions.append(session)
            
            # Sort by last activity (most recent first)
            sessions.sort(key=lambda s: s.last_activity, reverse=True)
            
            logger.debug(
                "Sessions listed",
                user_id=user_id,
                active_only=active_only,
                count=len(sessions)
            )
            
            return sessions
            
        except Exception as e:
            logger.error(
                "Failed to list sessions",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            raise SessionError(
                f"Failed to list sessions: {e}",
                operation="list_sessions"
            )
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.session_timeout_hours)
            expired_sessions = []
            
            # Find expired sessions
            for session_id, session in list(self._sessions.items()):
                if session.last_activity < cutoff_time:
                    expired_sessions.append(session_id)
            
            # End expired sessions
            cleanup_count = 0
            for session_id in expired_sessions:
                if await self.end_session(session_id):
                    cleanup_count += 1
            
            if cleanup_count > 0:
                logger.info(
                    "Expired sessions cleaned up",
                    cleaned_up=cleanup_count,
                    remaining_sessions=len(self._sessions)
                )
            
            return cleanup_count
            
        except Exception as e:
            logger.error(
                "Failed to cleanup expired sessions",
                error=str(e),
                exc_info=True
            )
            return 0
    
    async def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        
        try:
            active_sessions = len(self._sessions)
            total_messages = sum(s.message_count for s in self._sessions.values())
            total_tool_calls = sum(s.tool_calls_count for s in self._sessions.values())
            total_errors = sum(s.error_count for s in self._sessions.values())
            
            avg_duration = 0
            if self._sessions:
                avg_duration = sum(s.get_duration_minutes() for s in self._sessions.values()) / len(self._sessions)
            
            return {
                "active_sessions": active_sessions,
                "total_messages": total_messages,
                "total_tool_calls": total_tool_calls,
                "total_errors": total_errors,
                "average_session_duration_minutes": avg_duration,
                "session_timeout_hours": self.session_timeout_hours
            }
            
        except Exception as e:
            logger.error(
                "Failed to get session statistics",
                error=str(e),
                exc_info=True
            )
            return {}
    
    async def _persist_session(self, session: Session) -> None:
        """Persist session to storage."""
        
        try:
            session_file = self.storage_path / f"session_{session.session_id}.json"
            
            session_data = session.to_dict()
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
        except Exception as e:
            logger.error(
                "Failed to persist session",
                session_id=session.session_id,
                error=str(e)
            )
            # Don't raise - session can continue in memory
    
    async def _load_session(self, session_id: str) -> Optional[Session]:
        """Load session from storage."""
        
        try:
            session_file = self.storage_path / f"session_{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            session = Session.from_dict(session_data)
            
            # Load memory
            await session.memory.load_session()
            
            return session
            
        except Exception as e:
            logger.error(
                "Failed to load session from storage",
                session_id=session_id,
                error=str(e)
            )
            return None
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self.cleanup_interval_minutes * 60)
                    await self.cleanup_expired_sessions()
                except Exception as e:
                    logger.error(
                        "Error in session cleanup task",
                        error=str(e),
                        exc_info=True
                    )
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
        
        logger.info(
            "Session cleanup task started",
            cleanup_interval_minutes=self.cleanup_interval_minutes,
            session_timeout_hours=self.session_timeout_hours
        )
    
    async def shutdown(self):
        """Shutdown session manager."""
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Persist all active sessions
        for session in self._sessions.values():
            await self._persist_session(session)
        
        logger.info(
            "Session manager shutdown complete",
            persisted_sessions=len(self._sessions)
        )


# Global session manager instance
_global_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    
    global _global_session_manager
    
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    
    return _global_session_manager