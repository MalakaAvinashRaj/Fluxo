"""Log formatters for the autonomous agent system."""

import json
from typing import Dict, Any
from datetime import datetime


class JSONFormatter:
    """JSON log formatter for structured logging."""
    
    def __init__(self):
        pass
    
    def format(self, record: Dict[str, Any]) -> str:
        """Format log record as JSON."""
        
        formatted = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.get("level", "info").upper(),
            "message": record.get("message", ""),
            "logger": record.get("logger", ""),
            **record.get("context", {})
        }
        
        return json.dumps(formatted, separators=(',', ':'))


class StructuredFormatter:
    """Human-readable structured formatter for development."""
    
    def __init__(self):
        pass
    
    def format(self, record: Dict[str, Any]) -> str:
        """Format log record for human reading."""
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        level = record.get("level", "info").upper()
        message = record.get("message", "")
        logger_name = record.get("logger", "")
        
        base = f"{timestamp} [{level}] {logger_name}: {message}"
        
        # Add context if present
        context = record.get("context", {})
        if context:
            context_str = " ".join([f"{k}={v}" for k, v in context.items()])
            base += f" | {context_str}"
        
        return base