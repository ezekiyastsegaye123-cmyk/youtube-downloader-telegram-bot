"""Application entrypoint for the YouTube Downloader Telegram Bot."""

import asyncio
import logging
import os
import sys
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from bot.config import Config
from bot.handlers.commands import start_command, help_command, about_command
from bot.handlers.messages import handle_text_message
from bot.handlers.callbacks import handle_callback_query

# Configure standard logging
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("YouTubeDownloaderBot")

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and inform the user if possible."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ **An internal error occurred while processing your request.**\n"
                "Please try again in a few moments.",
                parse_mode="Markdown"
            )
        except Exception:
            pass

async def run_health_check_server(port: int) -> None:
    """Lightweight HTTP health check server for cloud platforms (e.g. Render Web Service)."""
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            await reader.read(1024)
            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/json\r\n"
                b"Content-Length: 18\r\n"
                b"Connection: close\r\n\r\n"
                b'{"status": "ok"}\n'
            )
            writer.write(response)
            await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    server = await asyncio.start_server(handle_client, "0.0.0.0", port)
    logger.info(f"Cloud health check server listening on 0.0.0.0:{port}")
    async with server:
        await server.serve_forever()

async def post_init(application) -> None:
    """Background startup tasks."""
    port_str = os.getenv("PORT", "").strip()
    if port_str and port_str.isdigit():
        port = int(port_str)
        asyncio.create_task(run_health_check_server(port))

def build_application():
    """Build and configure the Telegram application."""
    Config.validate()

    builder = ApplicationBuilder().token(Config.BOT_TOKEN).post_init(post_init)

    if Config.TELEGRAM_API_URL:
        logger.info(f"Using custom Telegram Bot API endpoint: {Config.TELEGRAM_API_URL}")
        builder = builder.base_url(Config.TELEGRAM_API_URL)

    app = builder.build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))

    # Register message handler for YouTube links
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Register inline callback handler
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # Register global error handler
    app.add_error_handler(global_error_handler)

    return app

def main() -> None:
    """Run the bot in long-polling mode."""
    try:
        app = build_application()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Please copy .env.example to .env and insert your Telegram Bot Token.")
        sys.exit(1)

    logger.info("Starting YouTube Downloader Telegram Bot...")
    if Config.ALLOWED_USERS:
        logger.info(f"Bot running in PRIVATE mode. Allowed users: {Config.ALLOWED_USERS}")
    else:
        logger.info("Bot running in PUBLIC mode.")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
