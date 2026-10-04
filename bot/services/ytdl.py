"""Media extraction and download service wrapping yt-dlp."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yt_dlp

from bot.config import Config

logger = logging.getLogger(__name__)

class VideoMetadata:
    """Structured representation of video metadata and selectable formats."""

    def __init__(
        self,
        video_id: str,
        title: str,
        duration: int,
        uploader: str,
        thumbnail: str,
        available_resolutions: List[Dict[str, Any]],
        audio_info: Dict[str, Any]
    ) -> None:
        self.video_id = video_id
        self.title = title
        self.duration = duration
        self.uploader = uploader
        self.thumbnail = thumbnail
        self.available_resolutions = available_resolutions
        self.audio_info = audio_info


def get_base_ydl_opts() -> Dict[str, Any]:
    """Build base yt-dlp options with cookies and proxy if configured."""
    opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extract_flat": False,
        "source_address": "0.0.0.0",  # bind to ipv4
        # Use mobile & embedded clients which bypass web bot verification challenges
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "mweb", "web"]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    if Config.COOKIES_FILE and os.path.exists(Config.COOKIES_FILE):
        opts["cookiefile"] = Config.COOKIES_FILE
        logger.info(f"Using cookies file: {Config.COOKIES_FILE}")

    if Config.PROXY_URL:
        opts["proxy"] = Config.PROXY_URL
        logger.info("Using configured proxy")

    return opts


def _sync_extract_info(url: str) -> VideoMetadata:
    """Synchronous worker to extract metadata and formats."""
    opts = get_base_ydl_opts()
    opts["skip_download"] = True

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("Could not retrieve video information from the URL.")

        video_id = info.get("id", "unknown")
        title = info.get("title", "YouTube Video")
        duration = info.get("duration", 0) or 0
        uploader = info.get("uploader", "Unknown Creator")
        thumbnail = info.get("thumbnail", "")

        # Find best audio size for combined estimation
        formats = info.get("formats", [])
        best_audio_size = 0
        audio_formats = [f for f in formats if f.get("vcodec") == "none" and f.get("acodec") != "none"]
        if audio_formats:
            # pick highest bitrate or largest audio
            best_audio = max(
                audio_formats,
                key=lambda f: (f.get("tbr") or 0, f.get("filesize") or f.get("filesize_approx") or 0)
            )
            best_audio_size = best_audio.get("filesize") or best_audio.get("filesize_approx") or 0

        # Target standard resolutions: 1080, 720, 480, 360, 240
        target_resolutions = [1080, 720, 480, 360, 240]
        detected_resolutions: Dict[int, Dict[str, Any]] = {}

        video_formats = [f for f in formats if f.get("vcodec") != "none"]

        for f in video_formats:
            w = f.get("width")
            h = f.get("height")
            if not h:
                continue

            # For vertical videos / Shorts, standard quality is determined by the shorter dimension
            effective_res = min(w, h) if w and h else h

            # Map to nearest or exact standard resolution bucket
            matched_bucket = None
            for target in target_resolutions:
                if effective_res >= target - 20 and effective_res <= target + 20:
                    matched_bucket = target
                    break

            if not matched_bucket:
                # If resolution is lower than 240, bucket as lowest or exact
                if effective_res < 240:
                    matched_bucket = effective_res
                else:
                    continue

            v_size = f.get("filesize") or f.get("filesize_approx") or 0
            has_audio = f.get("acodec") != "none"
            total_size = v_size if has_audio else (v_size + best_audio_size if v_size else 0)

            if matched_bucket not in detected_resolutions or total_size > detected_resolutions[matched_bucket]["size"]:
                detected_resolutions[matched_bucket] = {
                    "height": h,
                    "effective_res": matched_bucket,
                    "label": f"{matched_bucket}p",
                    "size": total_size,
                    "exceeds_limit": total_size > Config.MAX_FILE_SIZE_BYTES if total_size > 0 else False
                }

        # If no standard bucket matched, fallback to best available video format
        if not detected_resolutions and video_formats:
            best_vf = video_formats[-1]
            h = best_vf.get("height") or 360
            detected_resolutions[h] = {
                "height": h,
                "effective_res": h,
                "label": f"{h}p",
                "size": best_vf.get("filesize") or best_vf.get("filesize_approx") or 0,
                "exceeds_limit": False
            }

        # Sort available resolutions descending, limit to top 4 options
        available_res = sorted(
            detected_resolutions.values(),
            key=lambda x: x["effective_res"],
            reverse=True
        )[:4]

        # Audio info (MP3 ~192kbps estimate if size is not exact)
        estimated_mp3_size = best_audio_size
        if not estimated_mp3_size and duration > 0:
            # 192 kbps = 24 KB/s
            estimated_mp3_size = int(duration * 24 * 1024)

        audio_info = {
            "label": "MP3 Audio",
            "size": estimated_mp3_size,
            "exceeds_limit": estimated_mp3_size > Config.MAX_FILE_SIZE_BYTES if estimated_mp3_size > 0 else False
        }

        return VideoMetadata(
            video_id=video_id,
            title=title,
            duration=duration,
            uploader=uploader,
            thumbnail=thumbnail,
            available_resolutions=available_res,
            audio_info=audio_info
        )


async def extract_video_info(url: str) -> VideoMetadata:
    """Async wrapper to extract video information in thread."""
    return await asyncio.to_thread(_sync_extract_info, url)


def _sync_download(
    url: str,
    output_dir: Path,
    media_type: str,
    quality: str,
    progress_hook: Optional[Any] = None
) -> Path:
    """Synchronous worker to download and transcode media."""
    opts = get_base_ydl_opts()
    opts["outtmpl"] = str(output_dir / "%(title).80s_%(id)s.%(ext)s")
    opts["noplaylist"] = True

    if progress_hook:
        opts["progress_hooks"] = [progress_hook]

    if media_type == "audio":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    else:
        # Video download: select requested height
        height = quality if quality.isdigit() else "720"
        # Download bestvideo with height <= target + bestaudio, or fallback
        opts["format"] = (
            f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={height}]+bestaudio/"
            f"best[height<={height}]/best"
        )
        opts["merge_output_format"] = "mp4"

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        downloaded_path = Path(filename)

        if media_type == "audio":
            # Postprocessor changes extension to .mp3
            mp3_path = downloaded_path.with_suffix(".mp3")
            if mp3_path.exists():
                return mp3_path
            # Check if any .mp3 exists in output_dir
            mp3s = list(output_dir.glob("*.mp3"))
            if mp3s:
                return mp3s[0]

        # For video, check mp4 or existing file
        if downloaded_path.exists():
            return downloaded_path
        mp4_path = downloaded_path.with_suffix(".mp4")
        if mp4_path.exists():
            return mp4_path

        # Fallback to any media file in output_dir
        media_files = [f for f in output_dir.glob("*") if f.is_file() and not f.name.endswith(".part")]
        if media_files:
            return media_files[0]

        raise FileNotFoundError("Downloaded file could not be located in output directory.")


async def download_media(
    url: str,
    output_dir: Path,
    media_type: str,
    quality: str,
    progress_hook: Optional[Any] = None
) -> Path:
    """Async wrapper to download media in thread."""
    return await asyncio.to_thread(
        _sync_download,
        url=url,
        output_dir=output_dir,
        media_type=media_type,
        quality=quality,
        progress_hook=progress_hook
    )
