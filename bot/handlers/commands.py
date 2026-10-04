"""Command handlers for /start, /help, and /about."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.rate_limiter import concurrency_manager

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not update.effective_user or not update.effective_message:
        return

    user_id = update.effective_user.id
    if not concurrency_manager.is_user_allowed(user_id):
        await update.effective_message.reply_text(
            f"⛔ **Access Denied**: You are not authorized to use this bot.\n\n"
            f"🆔 **Your Telegram User ID:** `{user_id}`\n"
            "If you are the bot owner, add this ID to `ALLOWED_USERS` in your `.env` file.",
            parse_mode="Markdown"
        )
        return

    first_name = update.effective_user.first_name or "there"
    welcome_text = (
        f"👋 **Hello {first_name}! Welcome to YouTube Downloader Bot.**\n"
        f"🆔 **Your User ID:** `{user_id}`\n\n"
        "🎬 **How to use:**\n"
        "Simply send me any **YouTube video** or **YouTube Shorts** link!\n\n"
        "✨ **Features:**\n"
        "• 📺 Select from multiple video resolutions (360p, 720p, 1080p)\n"
        "• 🎵 Extract high-quality MP3 audio\n"
        "• ⚡ Real-time download progress bar\n"
        "• 🛡️ Anti-bot bypass with cookie/proxy support\n\n"
        "📌 *Note: Standard Telegram bots have a 50MB file size limit. Formats exceeding 50MB will be flagged with a warning.*\n\n"
        "Send a link now to try it out!"
    )
    await update.effective_message.reply_text(welcome_text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not update.effective_message:
        return

    help_text = (
        "📖 **YouTube Downloader Bot - Help Guide**\n\n"
        "1️⃣ **Sending a link:**\n"
        "Copy and paste any link from YouTube:\n"
        "`https://www.youtube.com/watch?v=...`\n"
        "`https://youtu.be/...`\n"
        "`https://www.youtube.com/shorts/...`\n\n"
        "2️⃣ **Selecting Format:**\n"
        "After sending the link, you will see the video preview with buttons for available video resolutions and MP3 audio.\n\n"
        "3️⃣ **File Size Limits:**\n"
        "Telegram's Bot API limits uploads to **50MB**. If a format exceeds 50MB, choose a lower resolution (e.g. 720p or 360p) or MP3 audio.\n\n"
        "4️⃣ **Concurrency:**\n"
        "To ensure stable service for everyone, each user can run 1 download at a time.\n\n"
        "💡 Need support? Check the project repository or contact the bot admin."
    )
    await update.effective_message.reply_text(help_text, parse_mode="Markdown")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command."""
    if not update.effective_message:
        return

    about_text = (
        "🤖 **YouTube Downloader Telegram Bot**\n\n"
        "• **Core Engine:** yt-dlp & FFmpeg\n"
        "• **Framework:** python-telegram-bot (v22+ Async)\n"
        "• **Features:** Video & Audio extraction, real-time throttled progress bar, auto-cleanup.\n"
        "• **Status:** Active & Ready\n"
    )
    await update.effective_message.reply_text(about_text, parse_mode="Markdown")
