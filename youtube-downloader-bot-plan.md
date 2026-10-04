# YouTube Downloader Telegram Bot Plan

## Goal
Build a production-ready YouTube Downloader Telegram Bot using `python-telegram-bot` and `yt-dlp` that accepts YouTube links, presents format choices via inline buttons, and delivers video or MP3 audio with live progress updates.

## Tasks
- [x] Task 1: Initialize project environment and dependencies (`.venv`, `requirements.txt`, `.env.example`, `.gitignore`) → Verify: `.venv/bin/python -c "import telegram, yt_dlp, dotenv; print('OK')"` returns OK
- [x] Task 2: Build configuration, URL validator, and per-user concurrency rate limiter (`bot/config.py`, `bot/utils/validators.py`, `bot/utils/rate_limiter.py`) → Verify: Unit test script confirms valid YouTube/Shorts detection, playlist flagging, and concurrency locking
- [x] Task 3: Implement download cleaner and throttled progress reporter (`bot/services/cleaner.py`, `bot/services/progress.py`) → Verify: Progress tracker updates text and percentage bars at throttled intervals
- [x] Task 4: Implement yt-dlp media service (`bot/services/ytdl.py`) for metadata extraction, format filtering (<50MB awareness), cookies, proxy, and audio/video download → Verify: CLI test script extracts metadata from a sample YouTube video and simulates format sizing
- [x] Task 5: Implement bot handlers (`bot/handlers/commands.py`, `bot/handlers/messages.py`, `bot/handlers/callbacks.py`) for `/start`, URL processing, interactive inline menus, and download callbacks → Verify: Module imports and handler dispatch logic pass syntax and type checks
- [x] Task 6: Implement application entrypoint with graceful shutdown and error handling (`main.py`) → Verify: `python main.py --help` or dry-run initialization loads handlers cleanly without errors
- [x] Task 7: Create containerization and documentation (`Dockerfile`, `docker-compose.yml`, `README.md`) → Verify: `docker compose config` validates the docker compose file and README contains complete setup instructions
- [x] Task 8: End-to-end integration and smoke verification → Verify: Run comprehensive automated test suite verifying extractor, validator, progress renderer, and bot initialization

## Done When
- [x] User can send any YouTube video or Shorts link and receive an interactive menu with title, duration, and format options.
- [x] Selected video or MP3 downloads with live progress feedback, uploads to Telegram, and immediately cleans up disk files.
- [x] File size limits (>50MB warnings), playlists warnings, concurrency locks, cookies, and proxy options are handled gracefully.

## Notes
- Standard Telegram Bot API caps uploads at 50MB; formats exceeding 50MB are tagged with a warning.
- Telegram message editing is throttled to once every 2–3 seconds to avoid rate limits.
- Temporary files are stored in `downloads/<uuid>` and deleted in `finally` blocks.
