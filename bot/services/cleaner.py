"""Temporary file and workspace cleanup service."""

import logging
import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator
from bot.config import Config

logger = logging.getLogger(__name__)

@asynccontextmanager
async def temp_download_workspace(prefix: str = "yt_") -> AsyncIterator[Path]:
    """
    Creates an isolated temporary folder inside the download directory for a single task.
    Automatically deletes the entire directory and its contents upon exit.
    """
    task_id = f"{prefix}{uuid.uuid4().hex[:10]}"
    workspace_dir = Config.DOWNLOAD_DIR / task_id
    workspace_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield workspace_dir
    finally:
        try:
            if workspace_dir.exists():
                shutil.rmtree(workspace_dir, ignore_errors=True)
                logger.info(f"Cleaned up temporary workspace: {workspace_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup directory {workspace_dir}: {e}")
