"""Log handlers for the autonomous agent system."""

import asyncio
from typing import Dict, Any, Optional
from pathlib import Path


class FileHandler:
    """File handler for logging to files."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def write(self, message: str) -> None:
        """Write message to file."""
        
        try:
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except Exception as e:
            # Fallback to console if file writing fails
            print(f"Log file write error: {e}")
            print(message)


class MetricsHandler:
    """Handler for metrics logging."""
    
    def __init__(self):
        self.metrics_buffer = []
    
    def handle_metric(self, metric: Dict[str, Any]) -> None:
        """Handle a metric entry."""
        
        self.metrics_buffer.append(metric)
        
        # Keep buffer limited
        if len(self.metrics_buffer) > 1000:
            self.metrics_buffer = self.metrics_buffer[-500:]
    
    def get_metrics(self) -> list:
        """Get current metrics buffer."""
        return self.metrics_buffer.copy()
    
    def clear_metrics(self) -> None:
        """Clear metrics buffer."""
        self.metrics_buffer.clear()