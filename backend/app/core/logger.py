import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings

# Prevent duplicate handlers by removing the default loguru handler
logger.remove()

# Resolve and create the directory for file logs
log_file_path = Path(settings.LOG_FILE)
log_file_path.parent.mkdir(parents=True, exist_ok=True)

# 1. Configure Console Logging (with color formatting)
logger.add(
    sys.stderr,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    enqueue=True,
)

# 2. Configure File Logging (without color tags, with rotation and retention)
logger.add(
    settings.LOG_FILE,
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
    compression="zip",
    enqueue=True,
)

logger.info(f"Logging initialized. Level: {settings.LOG_LEVEL}, File: {settings.LOG_FILE}")
