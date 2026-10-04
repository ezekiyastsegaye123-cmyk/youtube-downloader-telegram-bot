"""Comprehensive test suite for YouTube Downloader Telegram Bot."""

import asyncio
import os
import unittest
from pathlib import Path

from bot.config import Config
from bot.utils.validators import (
    is_youtube_url,
    is_playlist_url,
    extract_clean_youtube_url,
)
from bot.utils.rate_limiter import ConcurrencyManager
from bot.services.progress import (
    format_bytes,
    format_eta,
    render_progress_bar,
)
from bot.services.cleaner import temp_download_workspace
from main import build_application

class TestValidators(unittest.TestCase):
    """Test URL parsing, validation, and sanitization."""

    def test_standard_watch_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertTrue(is_youtube_url(url))
        res = extract_clean_youtube_url(url)
        self.assertIsNotNone(res)
        clean_url, vid = res
        self.assertEqual(vid, "dQw4w9WgXcQ")
        self.assertEqual(clean_url, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_short_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ?si=abcdef12345"
        self.assertTrue(is_youtube_url(url))
        clean_url, vid = extract_clean_youtube_url(url)
        self.assertEqual(vid, "dQw4w9WgXcQ")
        self.assertEqual(clean_url, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_shorts_url(self):
        url = "https://www.youtube.com/shorts/3jz_g3c8f8Q"
        self.assertTrue(is_youtube_url(url))
        clean_url, vid = extract_clean_youtube_url(url)
        self.assertEqual(vid, "3jz_g3c8f8Q")
        self.assertEqual(clean_url, "https://www.youtube.com/watch?v=3jz_g3c8f8Q")

    def test_playlist_detection(self):
        playlist_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrEnWoR732-DNn"
        self.assertTrue(is_playlist_url(playlist_url))

        pure_playlist = "https://www.youtube.com/playlist?list=PLrEnWoR732-DNn"
        self.assertTrue(is_playlist_url(pure_playlist))

        standard_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertFalse(is_playlist_url(standard_url))

    def test_invalid_urls(self):
        self.assertFalse(is_youtube_url("https://vimeo.com/123456"))
        self.assertFalse(is_youtube_url("https://google.com"))
        self.assertFalse(is_youtube_url("not a url"))
        self.assertIsNone(extract_clean_youtube_url("https://google.com"))


class TestConcurrencyAndAccess(unittest.TestCase):
    """Test user session locks and access rules."""

    def test_concurrency_lock(self):
        manager = ConcurrencyManager()
        user_id = 99999

        async def run_lock_test():
            async with manager.user_session(user_id) as acquired_first:
                self.assertTrue(acquired_first)
                # Second concurrent attempt while first is active must fail
                async with manager.user_session(user_id) as acquired_second:
                    self.assertFalse(acquired_second)

            # Once the first session exits, locking should succeed again
            async with manager.user_session(user_id) as acquired_third:
                self.assertTrue(acquired_third)

        asyncio.run(run_lock_test())

    def test_access_control_open_by_default(self):
        manager = ConcurrencyManager()
        self.assertTrue(manager.is_user_allowed(12345))


class TestProgressFormatting(unittest.TestCase):
    """Test string formatters for bytes, duration, and progress bar."""

    def test_format_bytes(self):
        self.assertEqual(format_bytes(500), "500.0 B")
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(1048576), "1.0 MB")
        self.assertEqual(format_bytes(1073741824), "1.0 GB")
        self.assertEqual(format_bytes(None), "N/A")

    def test_format_eta(self):
        self.assertEqual(format_eta(30), "00:30")
        self.assertEqual(format_eta(75), "01:15")
        self.assertEqual(format_eta(3665), "01:01:05")
        self.assertEqual(format_eta(None), "N/A")

    def test_render_progress_bar(self):
        bar_0 = render_progress_bar(0)
        self.assertIn("0.0%", bar_0)
        self.assertIn("░" * 10, bar_0)

        bar_50 = render_progress_bar(50)
        self.assertIn("50.0%", bar_50)
        self.assertIn("█████░░░░░", bar_50)

        bar_100 = render_progress_bar(100)
        self.assertIn("100.0%", bar_100)
        self.assertIn("█" * 10, bar_100)


class TestCleanerService(unittest.TestCase):
    """Test temporary directory creation and automatic cleanup."""

    def test_temp_workspace_cleanup(self):
        workspace_path = None

        async def run_cleaner_test():
            nonlocal workspace_path
            async with temp_download_workspace(prefix="test_") as path:
                workspace_path = path
                self.assertTrue(path.exists())
                # Create a dummy file inside
                test_file = path / "dummy.mp4"
                test_file.write_text("sample content")
                self.assertTrue(test_file.exists())

            # Outside context, path must be deleted
            self.assertFalse(workspace_path.exists())

        asyncio.run(run_cleaner_test())


class TestApplicationSetup(unittest.TestCase):
    """Test building the telegram application."""

    def test_build_application(self):
        os.environ["BOT_TOKEN"] = "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
        app = build_application()
        self.assertIsNotNone(app)
        # Check registered handler groups
        self.assertIn(0, app.handlers)
        self.assertGreaterEqual(len(app.handlers[0]), 5)


from bot.services.splitter import split_media_if_needed, get_media_duration
import subprocess

class TestMediaSplitter(unittest.TestCase):
    """Test media duration detection and automatic splitting."""

    def test_small_file_not_split(self):
        async def run_test():
            async with temp_download_workspace(prefix="test_split_small_") as ws:
                dummy = ws / "small.mp4"
                dummy.write_bytes(b"0" * 1024)  # 1 KB
                parts = await split_media_if_needed(dummy, ws, max_part_size_mb=46)
                self.assertEqual(len(parts), 1)
                self.assertEqual(parts[0], dummy)
        asyncio.run(run_test())

    def test_media_splitting_when_needed(self):
        async def run_test():
            async with temp_download_workspace(prefix="test_split_action_") as ws:
                media_file = ws / "test_audio.mp3"
                # Generate 20s test audio
                cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=20", "-c:a", "libmp3lame", str(media_file)]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                
                # Split with tiny threshold so it triggers split
                parts = await split_media_if_needed(media_file, ws, max_part_size_mb=0.05, estimated_duration=20)
                self.assertGreater(len(parts), 1)
                for part in parts:
                    self.assertTrue(part.exists())
                    self.assertGreater(part.stat().st_size, 0)
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
