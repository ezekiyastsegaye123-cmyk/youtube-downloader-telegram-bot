"""Configuration manager for the Telegram bot."""

import os
from pathlib import Path
from typing import Optional, Set
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    """Application configuration loaded from environment variables."""

    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

    # Comma-separated user IDs for whitelist access. Empty means public to all.
    _allowed_raw: str = os.getenv("ALLOWED_USERS", "").strip()
    ALLOWED_USERS: Set[int] = {
        int(uid.strip())
        for uid in _allowed_raw.split(",")
        if uid.strip().isdigit()
    } if _allowed_raw else set()

    # Optional custom Telegram Bot API URL (for local bot API servers)
    TELEGRAM_API_URL: Optional[str] = os.getenv("TELEGRAM_API_URL", "").strip() or None
    TELEGRAM_API_ID: Optional[str] = os.getenv("TELEGRAM_API_ID", "").strip() or None
    TELEGRAM_API_HASH: Optional[str] = os.getenv("TELEGRAM_API_HASH", "").strip() or None

    # Maximum file size allowed in megabytes (Default 2000 MB / 2 GB for local server and long videos)
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "2000").strip())
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    # Optional cookies file for YouTube anti-bot bypass
    COOKIES_FILE: Optional[str] = os.getenv("COOKIES_FILE", "").strip() or None

    # Optional proxy URL (http://... or socks5://...)
    PROXY_URL: Optional[str] = os.getenv("PROXY_URL", "").strip() or None

    # Ephemeral download directory
    DOWNLOAD_DIR: Path = Path(os.getenv("DOWNLOAD_DIR", "./downloads")).resolve()

    @classmethod
    def load(cls) -> None:
        """Reload configuration from environment variables."""
        cls.BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
        raw = os.getenv("ALLOWED_USERS", "").strip()
        cls.ALLOWED_USERS = {
            int(uid.strip())
            for uid in raw.split(",")
            if uid.strip().isdigit()
        } if raw else set()
        cls.TELEGRAM_API_URL = os.getenv("TELEGRAM_API_URL", "").strip() or None
        cls.TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "").strip() or None
        cls.TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "").strip() or None
        cls.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "2000").strip())
        cls.MAX_FILE_SIZE_BYTES = cls.MAX_FILE_SIZE_MB * 1024 * 1024
        cls.COOKIES_FILE = os.getenv("COOKIES_FILE", "").strip() or None
        cls.PROXY_URL = os.getenv("PROXY_URL", "").strip() or None
        cls.DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "./downloads")).resolve()

    @classmethod
    def validate(cls) -> None:
        """Validate critical configuration parameters."""
        cls.load()
        if not cls.BOT_TOKEN:
            raise ValueError(
                "BOT_TOKEN is not configured! Please set BOT_TOKEN in your .env file."
            )
        cls.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
