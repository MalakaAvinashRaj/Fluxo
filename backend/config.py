"""Configuration management for the autonomous agent system."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    host: str = Field(default="localhost", alias="AGENT_HOST")
    port: int = Field(default=8081, alias="AGENT_PORT")
    websocket_port: int = Field(default=9091, alias="AGENT_WS_PORT")
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    default_model: str = Field(default="gpt-5-nano", alias="DEFAULT_MODEL")
    max_tokens: int = Field(default=128000, alias="MAX_TOKENS")
    temperature: float = Field(default=0.1, alias="TEMPERATURE")
    
    # Memory Configuration
    max_context_size: int = Field(default=272000, alias="MAX_CONTEXT_SIZE")
    memory_cache_ttl: int = Field(default=3600, alias="MEMORY_CACHE_TTL")  # seconds
    
    # Tool Configuration
    tool_timeout: int = Field(default=30, alias="TOOL_TIMEOUT")  # seconds
    max_parallel_tools: int = Field(default=10, alias="MAX_PARALLEL_TOOLS")
    
    # Error Handling
    retry_attempts: int = Field(default=3, alias="RETRY_ATTEMPTS")
    retry_delay: float = Field(default=1.0, alias="RETRY_DELAY")  # seconds
    circuit_breaker_threshold: int = Field(default=5, alias="CIRCUIT_BREAKER_THRESHOLD")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="console", alias="LOG_FORMAT")  # json or text
    log_file: Optional[str] = Field(default=None, alias="LOG_FILE")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")
    metrics_port: int = Field(default=8082, alias="METRICS_PORT")
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    
    # Integration
    preview_server_url: str = Field(default="http://localhost:8080", alias="PREVIEW_SERVER_URL")
    session_storage_path: str = Field(default="./sessions", alias="SESSION_STORAGE_PATH")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True
    }


# Global settings instance
settings = Settings()