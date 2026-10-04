"""Media splitting service using FFmpeg to bypass Telegram's 50MB file limit."""

import asyncio
import logging
import math
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Default target chunk size in MB (kept under 48MB so Telegram accepts it without errors)
DEFAULT_MAX_CHUNK_MB = 46

def get_media_duration(file_path: Path) -> float:
    """Use ffprobe to determine the duration of the media file in seconds."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Could not determine media duration using ffprobe: {e}")
        return 0.0


async def split_media_if_needed(
    input_file: Path,
    output_dir: Path,
    max_part_size_mb: int = DEFAULT_MAX_CHUNK_MB,
    estimated_duration: Optional[int] = None
) -> List[Path]:
    """
    Checks the media file size. If larger than max_part_size_mb,
    slices the file into smaller parts using FFmpeg stream copying (-c copy).
    Returns a list of Path objects representing either [input_file] or the split parts.
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Media file not found: {input_file}")

    file_size = input_file.stat().st_size
    max_bytes = max_part_size_mb * 1024 * 1024

    if file_size <= max_bytes:
        return [input_file]

    logger.info(
        f"File {input_file.name} is {file_size / (1024 * 1024):.1f}MB (> {max_part_size_mb}MB). Splitting into parts..."
    )

    # Determine duration
    duration = estimated_duration or 0
    if duration <= 0:
        duration = int(get_media_duration(input_file))

    # Calculate target number of parts and segment time
    num_parts = max(2, math.ceil(file_size / max_bytes))
    if duration > 0:
        segment_time = max(5, int(duration / num_parts))
    else:
        # Fallback to 180 seconds if duration could not be determined
        segment_time = 180

    suffix = input_file.suffix.lower()
    split_dir = output_dir / "split_parts"
    split_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = split_dir / f"part_%03d{suffix}"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_file),
        "-c", "copy",
        "-map", "0",
        "-segment_time", str(segment_time),
        "-f", "segment",
        "-reset_timestamps", "1",
        str(output_pattern)
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        error_msg = stderr.decode(errors="ignore")
        logger.error(f"FFmpeg split failed: {error_msg}")
        raise RuntimeError(f"FFmpeg splitting failed: {error_msg[-300:]}")

    parts = sorted(split_dir.glob(f"part_*{suffix}"))
    if not parts:
        logger.warning("No split parts generated, returning original file")
        return [input_file]

    logger.info(f"Successfully split {input_file.name} into {len(parts)} parts")
    return parts
