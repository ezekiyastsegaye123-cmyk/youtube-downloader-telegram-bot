"""Message handler to receive and parse YouTube links."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.config import Config
from bot.utils.validators import is_youtube_url, is_playlist_url, extract_clean_youtube_url
from bot.utils.rate_limiter import concurrency_manager
from bot.services.ytdl import extract_video_info
from bot.services.progress import format_bytes, format_eta

logger = logging.getLogger(__name__)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process incoming text messages and extract YouTube links."""
    if not update.effective_user or not update.effective_message:
        return

    user_id = update.effective_user.id
    if not concurrency_manager.is_user_allowed(user_id):
        await update.effective_message.reply_text(
            "⛔ **Access Denied**: You are not authorized to use this bot.",
            parse_mode="Markdown"
        )
        return

    text = update.effective_message.text or ""

    if not is_youtube_url(text):
        await update.effective_message.reply_text(
            "ℹ️ Please send a valid **YouTube video** or **Shorts** link.\n\n"
            "Example: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`",
            parse_mode="Markdown"
        )
        return

    # Check for playlists
    is_playlist = is_playlist_url(text)

    clean_data = extract_clean_youtube_url(text)
    if not clean_data:
        await update.effective_message.reply_text(
            "❌ Could not recognize a valid YouTube video ID from the provided link.",
            parse_mode="Markdown"
        )
        return

    clean_url, video_id = clean_data

    # Send status message
    status_msg = await update.effective_message.reply_text(
        "🔍 **Fetching video details...** Please wait.",
        parse_mode="Markdown"
    )

    try:
        metadata = await extract_video_info(clean_url)
    except Exception as e:
        logger.error(f"Error extracting video metadata for {clean_url}: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ **Failed to retrieve video information.**\n\n_Reason:_ `{str(e)[:200]}`\n\n"
            "YouTube might be rate-limiting or this video might be age-restricted / private.",
            parse_mode="Markdown"
        )
        return

    # Cache metadata in user_data for callback access
    if context.user_data is not None:
        context.user_data[f"meta_{video_id}"] = {
            "url": clean_url,
            "title": metadata.title,
            "duration": metadata.duration,
            "uploader": metadata.uploader
        }

    # Build keyboard
    keyboard = []

    # Video buttons
    video_row = []
    for res in metadata.available_resolutions:
        size = res.get("size", 0)
        size_str = format_bytes(size) if size else ""
        split_hint = " ✂️" if size > 48 * 1024 * 1024 and not Config.TELEGRAM_API_URL else ""
        button_text = f"🎬 {res['label']} ({size_str}{split_hint})" if size_str else f"🎬 {res['label']}"
        callback_data = f"dl:v:{res['height']}:{video_id}"

        video_row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        if len(video_row) == 2:
            keyboard.append(video_row)
            video_row = []
    if video_row:
        keyboard.append(video_row)

    # Audio button
    audio_size = metadata.audio_info.get("size", 0)
    audio_size_str = format_bytes(audio_size) if audio_size else ""
    audio_split_hint = " ✂️" if audio_size > 48 * 1024 * 1024 and not Config.TELEGRAM_API_URL else ""
    audio_text = f"🎵 MP3 Audio ({audio_size_str}{audio_split_hint})" if audio_size_str else "🎵 MP3 Audio"
    keyboard.append([
        InlineKeyboardButton(
            audio_text,
            callback_data=f"dl:a:mp3:{video_id}"
        )
    ])

    # Cancel button
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{video_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    duration_str = format_eta(metadata.duration)
    playlist_warning = "\n\n⚠️ _Note: Playlists are not downloaded in batch. Only this video is selected._" if is_playlist else ""
    split_info = "\n\n✂️ _Files >50MB will be automatically split into seamless parts for Telegram delivery._" if not Config.TELEGRAM_API_URL else ""

    caption = (
        f"🎬 **{metadata.title}**\n\n"
        f"👤 **Channel:** {metadata.uploader}\n"
        f"⏱️ **Duration:** `{duration_str}`"
        f"{playlist_warning}"
        f"{split_info}\n\n"
        "👇 **Select your preferred format to download:**"
    )

    try:
        if metadata.thumbnail:
            await update.effective_message.reply_photo(
                photo=metadata.thumbnail,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text(
                caption,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.warning(f"Could not send thumbnail photo, falling back to text: {e}")
        await status_msg.edit_text(
            caption,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
