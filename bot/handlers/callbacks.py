"""Callback query handler for inline keyboard format selection."""

import logging
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import Config
from bot.utils.rate_limiter import concurrency_manager
from bot.services.cleaner import temp_download_workspace
from bot.services.progress import ThrottledProgressReporter, format_bytes
from bot.services.ytdl import download_media
from bot.services.splitter import split_media_if_needed

logger = logging.getLogger(__name__)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle format selection and cancellation callback buttons."""
    query = update.callback_query
    if not query or not query.data or not update.effective_user or not update.effective_chat:
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    data = query.data

    if not concurrency_manager.is_user_allowed(user_id):
        await query.answer("⛔ Access Denied", show_alert=True)
        return

    # Handle cancellation
    if data.startswith("cancel:"):
        await query.answer("Download cancelled.")
        try:
            await query.message.delete()
        except Exception:
            await query.edit_message_caption(caption="❌ **Cancelled.**", reply_markup=None)
        return

    # Handle download triggers: dl:<type>:<quality>:<video_id>
    if not data.startswith("dl:"):
        await query.answer()
        return

    parts = data.split(":")
    if len(parts) != 4:
        await query.answer("Invalid request.", show_alert=True)
        return

    _, media_flag, quality, video_id = parts
    is_audio = media_flag == "a"
    media_type = "audio" if is_audio else "video"
    canonical_url = f"https://www.youtube.com/watch?v={video_id}"

    # Retrieve cached metadata if available
    metadata = {}
    if context.user_data is not None:
        metadata = context.user_data.get(f"meta_{video_id}", {})

    title = metadata.get("title", f"YouTube_{video_id}")
    uploader = metadata.get("uploader", "YouTube")
    duration = metadata.get("duration", 0)

    # Check concurrency lock
    async with concurrency_manager.user_session(user_id) as acquired:
        if not acquired:
            await query.answer(
                "⏳ You already have an active download in progress. Please wait for it to complete.",
                show_alert=True
            )
            return

        await query.answer()

        action_label = "Audio (MP3)" if is_audio else f"Video ({quality}p)"
        progress_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"⏳ **Starting download for {action_label}...**\nPlease wait.",
            parse_mode="Markdown"
        )

        try:
            async with temp_download_workspace(prefix=f"task_{video_id}_") as workspace_dir:
                reporter = ThrottledProgressReporter(
                    message=progress_msg,
                    action_name=f"Downloading {action_label}"
                )

                # Download media using yt-dlp
                downloaded_file: Path = await download_media(
                    url=canonical_url,
                    output_dir=workspace_dir,
                    media_type=media_type,
                    quality=quality,
                    progress_hook=reporter.progress_hook
                )

                file_size = downloaded_file.stat().st_size
                # Absolute upper limit check (2GB default)
                if file_size > Config.MAX_FILE_SIZE_BYTES:
                    size_str = format_bytes(file_size)
                    max_str = format_bytes(Config.MAX_FILE_SIZE_BYTES)
                    await progress_msg.edit_text(
                        f"⚠️ **File size exceeds allowed limit!**\n\n"
                        f"Downloaded size: `{size_str}`\n"
                        f"Maximum limit: `{max_str}`\n\n"
                        f"👉 *Recommendation:* Please select a lower resolution or MP3 audio.",
                        parse_mode="Markdown"
                    )
                    return

                # If using local Bot API, single uploads up to 2000MB are supported.
                # If on standard Telegram cloud API, automatically split files >46MB into parts.
                max_single_upload_mb = 2000 if Config.TELEGRAM_API_URL else 46

                parts = [downloaded_file]
                if file_size > max_single_upload_mb * 1024 * 1024:
                    await progress_msg.edit_text(
                        f"✂️ **File is {format_bytes(file_size)} (>50MB).**\n"
                        "Splitting into parts for Telegram delivery with zero quality loss...\nPlease wait a moment.",
                        parse_mode="Markdown"
                    )
                    parts = await split_media_if_needed(
                        input_file=downloaded_file,
                        output_dir=workspace_dir,
                        max_part_size_mb=46,
                        estimated_duration=duration
                    )

                total_parts = len(parts)

                # Upload part(s) to Telegram
                for idx, part_file in enumerate(parts, start=1):
                    part_badge = f" [Part {idx}/{total_parts}]" if total_parts > 1 else ""
                    if total_parts > 1:
                        try:
                            await progress_msg.edit_text(
                                f"📤 **Uploading{part_badge} to Telegram...**\n"
                                f"Part size: `{format_bytes(part_file.stat().st_size)}`",
                                parse_mode="Markdown"
                            )
                        except Exception:
                            pass
                    else:
                        await reporter.notify_uploading()

                    with open(part_file, "rb") as media_stream:
                        if is_audio:
                            await context.bot.send_audio(
                                chat_id=chat_id,
                                audio=media_stream,
                                title=f"{title}{part_badge}",
                                performer=uploader,
                                duration=duration,
                                caption=f"🎵 **{title}**{part_badge}\n👤 {uploader}",
                                write_timeout=1800,
                                read_timeout=1800,
                                parse_mode="Markdown"
                            )
                        else:
                            await context.bot.send_video(
                                chat_id=chat_id,
                                video=media_stream,
                                caption=f"🎬 **{title}**{part_badge}",
                                duration=duration,
                                supports_streaming=True,
                                write_timeout=1800,
                                read_timeout=1800,
                                parse_mode="Markdown"
                            )

                # Cleanup status message
                try:
                    await progress_msg.delete()
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Failed to download/send media for {canonical_url}: {e}", exc_info=True)
            try:
                await progress_msg.edit_text(
                    f"❌ **Download failed.**\n\n_Error:_ `{str(e)[:250]}`",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
