"""URL validation and sanitization for YouTube links."""

import re
from typing import Optional, Tuple

# Regex to detect standard YouTube video, Shorts, or youtu.be links
YOUTUBE_URL_PATTERN = re.compile(
    r'(https?://)?(www\.|m\.)?(youtube\.com/(watch\?v=|shorts/|live/)|youtu\.be/)([\w-]{11})',
    re.IGNORECASE
)

# Regex to detect playlist URLs
PLAYLIST_PATTERN = re.compile(r'[?&]list=([a-zA-Z0-9_-]+)', re.IGNORECASE)

def is_youtube_url(text: str) -> bool:
    """Check if the provided string contains a valid YouTube link."""
    return bool(YOUTUBE_URL_PATTERN.search(text))

def is_playlist_url(text: str) -> bool:
    """Check if the link contains a playlist parameter."""
    return bool(PLAYLIST_PATTERN.search(text)) or "youtube.com/playlist" in text

def extract_clean_youtube_url(text: str) -> Optional[Tuple[str, str]]:
    """
    Extract the clean canonical YouTube video URL and the 11-char video ID.
    Returns (clean_url, video_id) or None if no match.
    Strips tracking query parameters (&si=, &feature=, etc.).
    """
    match = YOUTUBE_URL_PATTERN.search(text)
    if not match:
        return None

    video_id = match.group(5)
    clean_url = f"https://www.youtube.com/watch?v={video_id}"
    return clean_url, video_id
