"""Memory management and context preservation for the autonomous agent system."""

import json
import hashlib
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import aiofiles
import structlog

from config import settings
from errors.exceptions import MemoryError

logger = structlog.get_logger()


@dataclass
class Message:
    """Represents a conversation message."""
    role: str  # user, assistant, system, tool
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ToolCall:
    """Represents a tool call and its result."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool call to dictionary."""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolCall':
        """Create tool call from dictionary."""
        if data.get('timestamp'):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class MemoryManager:
    """Manages conversation history and context preservation."""
    
    def __init__(
        self, 
        session_id: str,
        max_context_size: Optional[int] = None,
        storage_path: Optional[str] = None
    ):
        self.session_id = session_id
        self.max_context_size = max_context_size or settings.max_context_size
        self.storage_path = Path(storage_path or settings.session_storage_path)
        
        self.messages: List[Message] = []
        self.tool_calls_cache: Dict[str, ToolCall] = {}
        self.context_summary: Optional[str] = None
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    async def add_message(
        self, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add a message to conversation history."""
        
        try:
            message = Message(
                role=role,
                content=content,
                timestamp=datetime.utcnow(),
                metadata=metadata,
                tool_calls=tool_calls,
                tool_results=tool_results
            )
            
            self.messages.append(message)
            
            # Manage context size
            await self._manage_context_size()
            
            # Persist to storage
            await self._persist_session()
            
            logger.debug(
                "Message added to memory",
                session_id=self.session_id,
                role=role,
                message_count=len(self.messages),
                content_length=len(content) if content else 0
            )
            
        except Exception as e:
            logger.error(
                "Failed to add message to memory",
                session_id=self.session_id,
                error=str(e),
                exc_info=True
            )
            raise MemoryError(f"Failed to add message: {e}", "add_message")
    
    async def get_conversation_history(
        self, 
        include_system: bool = True,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation history formatted for LLM."""
        
        try:
            messages = self.messages.copy()
            
            # Filter system messages if requested
            if not include_system:
                messages = [m for m in messages if m.role != 'system']
            
            # Limit message count if specified
            if max_messages and len(messages) > max_messages:
                messages = messages[-max_messages:]
            
            # Convert to LLM format
            formatted_messages = []
            for message in messages:
                formatted_message = {
                    "role": message.role,
                    "content": message.content
                }
                
                # Add tool calls if present
                if message.tool_calls:
                    formatted_message["tool_calls"] = message.tool_calls
                
                # Add tool results if present  
                if message.tool_results:
                    formatted_message["tool_call_id"] = message.tool_results[0].get("call_id")
                
                # Add tool_call_id from metadata for tool messages
                if message.role == "tool" and message.metadata and "tool_call_id" in message.metadata:
                    formatted_message["tool_call_id"] = message.metadata["tool_call_id"]
                
                formatted_messages.append(formatted_message)
            
            logger.debug(
                "Retrieved conversation history",
                session_id=self.session_id,
                message_count=len(formatted_messages),
                include_system=include_system
            )
            
            return formatted_messages
            
        except Exception as e:
            logger.error(
                "Failed to get conversation history",
                session_id=self.session_id,
                error=str(e),
                exc_info=True
            )
            raise MemoryError(f"Failed to get history: {e}", "get_conversation_history")
    
    async def cache_tool_call(self, tool_call: ToolCall) -> str:
        """Cache a tool call result for reuse."""
        
        try:
            # Generate cache key from tool name and arguments
            cache_key = self._generate_cache_key(tool_call.tool_name, tool_call.arguments)
            
            tool_call.timestamp = datetime.utcnow()
            self.tool_calls_cache[cache_key] = tool_call
            
            logger.debug(
                "Tool call cached",
                session_id=self.session_id,
                tool_name=tool_call.tool_name,
                cache_key=cache_key
            )
            
            return cache_key
            
        except Exception as e:
            logger.error(
                "Failed to cache tool call",
                session_id=self.session_id,
                tool_name=tool_call.tool_name,
                error=str(e)
            )
            raise MemoryError(f"Failed to cache tool call: {e}", "cache_tool_call")
    
    async def get_cached_tool_result(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Optional[ToolCall]:
        """Get cached tool result if available and not expired."""
        
        try:
            cache_key = self._generate_cache_key(tool_name, arguments)
            
            if cache_key not in self.tool_calls_cache:
                return None
            
            cached_call = self.tool_calls_cache[cache_key]
            
            # Check if cache entry is expired
            if cached_call.timestamp:
                cache_age = datetime.utcnow() - cached_call.timestamp
                if cache_age > timedelta(seconds=settings.memory_cache_ttl):
                    # Remove expired entry
                    del self.tool_calls_cache[cache_key]
                    logger.debug(
                        "Expired cache entry removed",
                        session_id=self.session_id,
                        tool_name=tool_name,
                        cache_key=cache_key,
                        age_seconds=cache_age.total_seconds()
                    )
                    return None
            
            logger.debug(
                "Cache hit for tool call",
                session_id=self.session_id,
                tool_name=tool_name,
                cache_key=cache_key
            )
            
            return cached_call
            
        except Exception as e:
            logger.error(
                "Failed to get cached tool result",
                session_id=self.session_id,
                tool_name=tool_name,
                error=str(e)
            )
            return None
    
    async def _manage_context_size(self) -> None:
        """Manage context size by summarizing old messages if needed."""
        
        if len(self.messages) <= self.max_context_size:
            return
        
        try:
            # Keep recent messages and summarize older ones
            recent_messages = self.messages[-self.max_context_size // 2:]
            old_messages = self.messages[:-self.max_context_size // 2]
            
            # Create summary of old messages
            summary_content = self._create_summary(old_messages)
            
            # Create summary message
            summary_message = Message(
                role="system",
                content=f"[Previous conversation summary: {summary_content}]",
                timestamp=datetime.utcnow(),
                metadata={"type": "summary", "summarized_messages": len(old_messages)}
            )
            
            # Replace old messages with summary
            self.messages = [summary_message] + recent_messages
            self.context_summary = summary_content
            
            logger.info(
                "Context size managed with summarization",
                session_id=self.session_id,
                old_message_count=len(old_messages),
                remaining_message_count=len(self.messages)
            )
            
        except Exception as e:
            logger.error(
                "Failed to manage context size",
                session_id=self.session_id,
                error=str(e)
            )
            # Don't raise error - continue with oversized context
    
    def _create_summary(self, messages: List[Message]) -> str:
        """Create a summary of messages."""
        
        # Simple summary - in production, this could use LLM summarization
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]
        tool_calls = [m for m in messages if m.tool_calls]
        
        return (
            f"User asked {len(user_messages)} questions, "
            f"assistant provided {len(assistant_messages)} responses, "
            f"executed {len(tool_calls)} tool calls. "
            f"Key topics: {self._extract_topics(messages)}"
        )
    
    def _extract_topics(self, messages: List[Message]) -> str:
        """Extract key topics from messages."""
        
        # Simple keyword extraction - could be improved with NLP
        all_content = " ".join([m.content[:100] for m in messages if m.role in ["user", "assistant"]])
        
        # Return first 100 characters as summary
        return all_content[:100] + "..." if len(all_content) > 100 else all_content
    
    def _generate_cache_key(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Generate cache key for tool call."""
        
        # Create deterministic hash of tool name and arguments
        data = json.dumps({"tool": tool_name, "args": arguments}, sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()
    
    async def _persist_session(self) -> None:
        """Persist session data to storage."""
        
        try:
            session_file = self.storage_path / f"{self.session_id}.json"
            
            session_data = {
                "session_id": self.session_id,
                "messages": [m.to_dict() for m in self.messages],
                "tool_calls_cache": {k: v.to_dict() for k, v in self.tool_calls_cache.items()},
                "context_summary": self.context_summary,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            async with aiofiles.open(session_file, 'w') as f:
                await f.write(json.dumps(session_data, indent=2))
                
        except Exception as e:
            logger.error(
                "Failed to persist session",
                session_id=self.session_id,
                error=str(e)
            )
            # Don't raise error - session can continue in memory
    
    async def load_session(self) -> bool:
        """Load session data from storage."""
        
        try:
            session_file = self.storage_path / f"{self.session_id}.json"
            
            if not session_file.exists():
                logger.info(
                    "No existing session found, starting fresh",
                    session_id=self.session_id
                )
                return False
            
            async with aiofiles.open(session_file, 'r') as f:
                session_data = json.loads(await f.read())
            
            # Restore messages
            self.messages = [Message.from_dict(m) for m in session_data.get("messages", [])]
            
            # Restore tool calls cache
            cached_calls = session_data.get("tool_calls_cache", {})
            self.tool_calls_cache = {k: ToolCall.from_dict(v) for k, v in cached_calls.items()}
            
            # Restore context summary
            self.context_summary = session_data.get("context_summary")
            
            logger.info(
                "Session loaded successfully",
                session_id=self.session_id,
                message_count=len(self.messages),
                cached_calls=len(self.tool_calls_cache)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to load session",
                session_id=self.session_id,
                error=str(e)
            )
            return False