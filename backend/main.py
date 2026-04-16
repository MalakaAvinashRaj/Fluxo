"""Main entry point for the autonomous agent system."""

import asyncio
from pathlib import Path
import uvicorn
import structlog

from config import settings
from agent_logging.logger import setup_logging
from api import app

logger = structlog.get_logger()


async def main():
    """Main application entry point."""
    
    # Setup logging
    setup_logging()
    
    logger.info(
        "Starting Autonomous Agent System",
        version="1.0.0",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        default_model=settings.default_model
    )
    
    # Ensure required directories exist
    Path(settings.session_storage_path).mkdir(parents=True, exist_ok=True)
    
    # Run the server
    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_config=None,  # Use our structured logging
        access_log=False  # We handle access logging in middleware
    )
    
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error("Server error", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())