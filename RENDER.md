# 🚀 Deploying to Render.com (100% Free)

This guide shows you how to deploy the YouTube Downloader Telegram Bot to [Render.com](https://render.com) for **free**, with unrestricted YouTube downloading and 24/7 uptime.

---

## 🌟 Why Render?
- **Unrestricted Internet:** Downloads from YouTube and `yt-dlp` work out-of-the-box.
- **Docker-native:** Automatically builds our `Dockerfile` with FFmpeg.
- **Free Web Service Tier:** Our bot includes a built-in health-check server listening on `$PORT` so it runs seamlessly on Render's **Free Web Service** tier!

---

## 🛠️ Step-by-Step Deployment

### 1. Push Code to GitHub
Ensure the project is pushed to your GitHub account (already set up).

---

### 2. Create a Free Render Account
Go to [render.com](https://render.com) and sign up / log in with your GitHub account.

---

### 3. Create a New Web Service
1. In your Render dashboard, click the **New +** button in the top right.
2. Choose **Web Service**.
3. Select **Build and deploy from a Git repository** and click **Next**.
4. Find and connect your `youtube-downloader-telegram-bot` repository.

---

### 4. Configure the Web Service
Configure the settings on the page:
- **Name:** `yt-downloader-bot` (or any name you prefer)
- **Region:** Choose the region closest to you (e.g., Frankfurt, Oregon, Ohio, Singapore)
- **Branch:** `main`
- **Runtime:** **Docker**
- **Instance Type:** Select **Free** ($0/month)

---

### 5. Add Environment Variables
Scroll down to the **Environment Variables** section and click **Add Environment Variable**:

| Key | Value | Description |
| :--- | :--- | :--- |
| `BOT_TOKEN` | `your_bot_token_here` | Your Telegram Bot token from @BotFather |
| `ALLOWED_USERS` | `your_telegram_user_id` | Your Telegram numeric ID (e.g. `123456789`) |
| `MAX_FILE_SIZE_MB` | `50` | Maximum file download size (Telegram standard is 50MB) |

---

### 6. Deploy!
Click **Deploy Web Service**.
Render will:
1. Pull your code from GitHub.
2. Build the Docker container (installing Python and FFmpeg).
3. Start the bot and verify the health check on `$PORT`.
4. Your bot is now **live 24/7**!

Open Telegram, send `/start` to your bot, and send a YouTube link to download videos or MP3 audio!
