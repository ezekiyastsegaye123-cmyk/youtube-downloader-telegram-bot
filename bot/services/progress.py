"""Throttled progress tracking and progress bar formatting for Telegram."""

import asyncio
import time
import logging
from typing import Optional, Callable, Any
from telegram import Message
from telegram.error import BadRequest, TelegramError

logger = logging.getLogger(__name__)

def format_bytes(num_bytes: Optional[float]) -> str:
    """Format bytes to human-readable string (KB, MB, GB)."""
    if num_bytes is None or num_bytes <= 0:
        return "N/A"
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"

def format_eta(seconds: Optional[int]) -> str:
    """Format seconds into MM:SS format."""
    if seconds is None or seconds < 0:
        return "N/A"
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:02d}:{sec:02d}"

def render_progress_bar(percentage: float, length: int = 10) -> str:
    """Render a text progress bar like [▓▓▓▓░░░░░░]."""
    clamped = max(0.0, min(100.0, percentage))
    filled_len = int(round(length * (clamped / 100.0)))
    bar = "█" * filled_len + "░" * (length - filled_len)
    return f"[{bar}] {clamped:.1f}%"

class ThrottledProgressReporter:
    """
    Tracks yt-dlp download progress and updates Telegram status message
    throttled to at most once every `update_interval` seconds.
    """

    def __init__(
        self,
        message: Message,
        action_name: str = "Downloading",
        update_interval: float = 2.5
    ) -> None:
        self.message = message
        self.action_name = action_name
        self.update_interval = update_interval
        self.last_update_time = 0.0
        self.last_text = ""
        self._loop = asyncio.get_event_loop()

    def progress_hook(self, d: dict) -> None:
        """Synchronous progress hook invoked by yt-dlp."""
        status = d.get("status")
        now = time.time()

        if status == "downloading":
            if now - self.last_update_time < self.update_interval:
                return

            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            speed = d.get("speed")
            eta = d.get("eta")

            if total and total > 0:
                percent = (downloaded / total) * 100.0
                bar = render_progress_bar(percent)
                size_info = f"{format_bytes(downloaded)} / {format_bytes(total)}"
            else:
                bar = render_progress_bar(0.0)
                size_info = f"{format_bytes(downloaded)} / unknown"

            speed_info = f"{format_bytes(speed)}/s" if speed else "N/A"
            eta_info = format_eta(eta)

            text = (
                f"📥 **{self.action_name}...**\n\n"
                f"{bar}\n"
                f"📦 **Size:** `{size_info}`\n"
                f"⚡ **Speed:** `{speed_info}`\n"
                f"⏱️ **ETA:** `{eta_info}`"
            )

            self.last_update_time = now
            self.schedule_update(text)

        elif status == "finished":
            text = "⚙️ **Processing and muxing media with ffmpeg...**\nPlease wait..."
            self.schedule_update(text)

    def schedule_update(self, text: str) -> None:
        """Schedule an asynchronous message update on the running event loop."""
        if text == self.last_text:
            return
        self.last_text = text

        if self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._update_telegram(text), self._loop)

    async def _update_telegram(self, text: str) -> None:
        """Safely edit the Telegram message ignoring duplicate or rate-limit warnings."""
        try:
            await self.message.edit_text(text, parse_mode="Markdown")
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.debug(f"BadRequest when editing progress message: {e}")
        except TelegramError as e:
            logger.debug(f"Telegram error during progress update: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error updating progress: {e}")

    async def notify_uploading(self) -> None:
        """Explicitly notify user that upload to Telegram has begun."""
        text = (
            "📤 **Uploading to Telegram...**\n"
            "This may take a moment depending on file size."
        )
        await self._update_telegram(text)
