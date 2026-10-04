# 🚀 Solution B: Self-Hosted Telegram Bot API Server (2 GB Uploads)

By default, Telegram's official cloud servers (`https://api.telegram.org`) enforce a **50 MB** file upload cap on standard bots. 

By running a **Local Telegram Bot API Server**, you unlock:
- 📦 **File Upload Limit Raised to 2,000 MB (2 GB):** Easily download full 3–4 hour long videos, lectures, and movies!
- ⚡ **Faster Upload Speeds:** Upload directly to your local server without remote cloud bottlenecks.
- ⏱️ **Extended Timeouts:** Up to 30 minutes for uninterrupted uploads.

---

## 🔑 Step 1: Get Your Telegram `API_ID` and `API_HASH`

Telegram requires developer credentials to run a local Bot API server. You can obtain them in 1 minute:

1. Log in to [my.telegram.org](https://my.telegram.org) using your Telegram phone number.
2. Click on **API development tools**.
3. Fill in the short form:
   - **App title:** `YTDownloaderBot` (or anything you like)
   - **Short name:** `ytdlbot`
4. Click **Create application**.
5. Copy your **`api_id`** (numbers) and **`api_hash`** (alphanumeric string).

---

## 🐳 Step 2: Running with Docker Compose (Recommended)

The included [docker-compose.yml](file:///home/hezekiah/YT%20downlaoder%20telegram%20bot%20based%20on%20the%20link/docker-compose.yml) is pre-configured to run both the **Telegram Bot API server** and your **YouTube Downloader Bot** together:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and fill in your values:
   ```dotenv
   BOT_TOKEN=your_bot_token_from_botfather
   ALLOWED_USERS=your_telegram_user_id

   # Credentials from my.telegram.org:
   TELEGRAM_API_ID=12345678
   TELEGRAM_API_HASH=abcdef0123456789abcdef0123456789

   # Point to the local server in docker-compose:
   TELEGRAM_API_URL=http://telegram-bot-api:8081/bot
   MAX_FILE_SIZE_MB=2000
   ```
3. Start both services:
   ```bash
   docker compose up -d
   ```
4. Check the logs:
   ```bash
   docker compose logs -f
   ```

Both the local API server and the bot will start, allowing you to download videos up to **2 GB** directly in Telegram!

---

## 💻 Step 3: Running Locally on Linux (Without Docker)

If you prefer to run the binary directly on your Linux VPS:

1. Download the static build of `telegram-bot-api`:
   ```bash
   # Or install via package manager on Arch/Debian, or use Docker
   docker run -d --name telegram-bot-api-server \
     --restart unless-stopped \
     -p 8081:8081 \
     -e TELEGRAM_API_ID="your_api_id" \
     -e TELEGRAM_API_HASH="your_api_hash" \
     -e TELEGRAM_LOCAL=true \
     -v telegram-bot-api-data:/var/lib/telegram-bot-api \
     aiogram/telegram-bot-api:latest
   ```
2. In your `.env` file:
   ```dotenv
   TELEGRAM_API_URL=http://localhost:8081/bot
   MAX_FILE_SIZE_MB=2000
   ```
3. Run the bot:
   ```bash
   .venv/bin/python main.py
   ```

---

## 🎬 Testing 3–4 Hour Videos

Once your local server is running:
1. Send any long YouTube video (e.g. 3–4 hour podcast, documentary, livestream replay).
2. The bot will show format buttons with their actual sizes (e.g., `🎬 720p (1.2 GB)`).
3. Tap the button: the bot will download the stream, mux it with FFmpeg, and upload the full file up to **2 GB** straight to your Telegram chat!
