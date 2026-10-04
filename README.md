# 🎬 YouTube Downloader Telegram Bot

A production-ready Telegram Bot built with Python (`python-telegram-bot` v22+ async) and `yt-dlp` to download YouTube videos and extract MP3 audio directly within Telegram.

---

## ✨ Features

- 🔗 **Smart Link Detection:** Recognizes standard YouTube video URLs (`youtube.com/watch?v=...`, `youtu.be/...`) and YouTube Shorts (`youtube.com/shorts/...`).
- 🔘 **Interactive Inline Menu:** Sends video preview with thumbnail, duration, channel name, and format buttons.
- 📺 **Multiple Resolutions:** Choose from available qualities (1080p, 720p, 480p, 360p).
- 🎵 **High-Quality Audio Extraction:** Converts video audio to 192kbps MP3 with full metadata.
- ⚡ **Real-Time Progress Bar:** Displays throttled download speed, ETA, and progress bar (`[████░░░░] 50%`) without hitting Telegram API rate limits.
- ⚠️ **File Size Awareness:** Proactively flags options exceeding Telegram's 50MB bot upload limit, recommending optimal alternatives.
- 🔒 **User Concurrency & Access Control:** Restricts users to 1 concurrent download to prevent server overload; optional whitelist mode (`ALLOWED_USERS`).
- 🛡️ **Anti-Bot Resilience:** Built-in support for `cookies.txt` and HTTP/SOCKS5 proxy settings to bypass YouTube bot detection.
- 🧹 **Zero Disk Leakage:** Ephemeral temporary directory per download that is guaranteed to be deleted immediately upon file delivery or error.
- 🐳 **Docker-Ready:** Includes `Dockerfile` and `docker-compose.yml` for 1-command deployment.

---

## 📋 Requirements

- **Python:** 3.11+ (Python 3.12 or 3.13 recommended)
- **FFmpeg:** Installed and available in your system `$PATH` (required for audio extraction and video muxing)
- **Telegram Bot Token:** From [@BotFather](https://t.me/BotFather)

---

## 🚀 Quick Start (Local Virtualenv)

### 1. Clone or Open the Repository
```bash
cd "YT downlaoder telegram bot based on the link"
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Ensure FFmpeg is Installed
- **Ubuntu/Debian:** `sudo apt update && sudo apt install -y ffmpeg`
- **Arch Linux:** `sudo pacman -S ffmpeg`
- **Fedora/RHEL:** `sudo dnf install ffmpeg`
- **macOS:** `brew install ffmpeg`

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your editor of choice:
```dotenv
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
```

### 5. Launch the Bot
```bash
python main.py
```

---

## 🐳 Running with Docker

### 1. Configure `.env`
Make sure `.env` has your `BOT_TOKEN`:
```bash
cp .env.example .env
# Edit .env with your token
```

### 2. Start the Container
```bash
docker compose up -d --build
```

### 3. View Logs
```bash
docker compose logs -f
```

### 4. Stop the Container
```bash
docker compose down
```

---

## ⚙️ Configuration Parameters (`.env`)

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `BOT_TOKEN` | String | *Required* | Telegram Bot API token from @BotFather |
| `ALLOWED_USERS` | String | `""` (Empty) | Comma-separated Telegram User IDs allowed to use the bot. If empty, the bot is public to all users. |
| `MAX_FILE_SIZE_MB` | Integer | `50` | Maximum file size in MB allowed to download. Telegram's standard Bot API upload limit is 50MB. |
| `TELEGRAM_API_URL` | String | `""` | Custom Telegram Bot API URL (e.g. `http://localhost:8081/bot`) if running a local Bot API server (allows up to 2GB uploads). |
| `COOKIES_FILE` | String | `""` | Path to a `cookies.txt` file exported from a browser to authenticate with YouTube and bypass bot verification. |
| `PROXY_URL` | String | `""` | Proxy address for `yt-dlp` (e.g. `http://user:pass@ip:port` or `socks5://ip:port`). |
| `DOWNLOAD_DIR` | String | `./downloads` | Path for temporary download workspaces. |

---

## 🍪 How to Use Cookies (Anti-Bot Bypass)

If YouTube blocks downloads on your server IP (e.g., Datacenter IP / "Sign in to confirm you're not a bot"):
1. Install a browser extension like **Get cookies.txt LOCALLY** on Chrome/Firefox.
2. Visit YouTube while logged in and export the cookies to `cookies.txt`.
3. Place `cookies.txt` into the project root directory.
4. Set in `.env`:
   ```dotenv
   COOKIES_FILE=./cookies.txt
   ```
5. If using Docker, uncomment the cookies volume mapping in `docker-compose.yml`.

---

## 📁 Project Architecture

```
.
├── bot/
│   ├── __init__.py
│   ├── config.py             # Loads and validates environment variables
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py       # Handles /start, /help, /about
│   │   ├── messages.py       # Validates links, queries metadata, sends inline UI
│   │   └── callbacks.py      # Executes download, progress reporting & delivery
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ytdl.py           # yt-dlp wrapper, format filtering & download pipeline
│   │   ├── progress.py       # Throttled progress hooks and progress bar rendering
│   │   └── cleaner.py        # Ephemeral directory lifecycle management
│   └── utils/
│       ├── __init__.py
│       ├── validators.py     # Regex and URL sanitization
│       └── rate_limiter.py   # Per-user concurrency locking & whitelist
├── downloads/                # Ephemeral downloads folder (auto-cleaned)
├── .env.example              # Template configuration
├── Dockerfile                # Production container definition
├── docker-compose.yml        # Docker compose configuration
├── requirements.txt          # Python dependencies
├── main.py                   # Application entrypoint
└── README.md                 # Documentation
```

---

## 🛡️ License

This project is open-source and available under the [MIT License](LICENSE).
