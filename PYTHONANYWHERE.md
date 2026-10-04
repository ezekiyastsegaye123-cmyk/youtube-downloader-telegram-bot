# 🐍 Deploying to PythonAnywhere

This guide provides step-by-step instructions for hosting the YouTube Downloader Telegram Bot on [PythonAnywhere](https://www.pythonanywhere.com/).

---

## ⚠️ Important Note on PythonAnywhere Account Types

### 1. Free Accounts
- **Outbound Internet Whitelist:** Free PythonAnywhere accounts only allow HTTP/HTTPS traffic to an approved whitelist of domains. While Telegram (`api.telegram.org`) is whitelisted, **YouTube (`youtube.com` and `googlevideo.com`) is NOT whitelisted**.
  - If you are on a free account, `yt-dlp` will fail to download videos unless you configure an external proxy via `PROXY_URL` in `.env`.
- **Always-on Tasks:** Free accounts do not support Always-On tasks. Regular bash consoles are killed after a period of inactivity.

### 2. Paid Accounts (Hacker Plan or higher, ~$5/month)
- Full, unrestricted outbound internet access (YouTube and `yt-dlp` work directly).
- Includes the **Always-On Tasks** feature to keep the bot running 24/7 automatically with automatic restarts if it crashes.

---

## 🚀 Setup Steps on PythonAnywhere

### Step 1: Open a Bash Console
1. Log in to your PythonAnywhere account.
2. Go to the **Consoles** tab and start a **Bash** console.

---

### Step 2: Install FFmpeg (Static Build)
Since PythonAnywhere does not provide `sudo` access, install a static Linux binary of FFmpeg into your local user directory:

```bash
mkdir -p ~/.local/bin
cd /tmp
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz
cp ffmpeg-*-amd64-static/ffmpeg ffmpeg-*-amd64-static/ffprobe ~/.local/bin/
chmod +x ~/.local/bin/ffmpeg ~/.local/bin/ffprobe
rm -rf /tmp/ffmpeg*
```

Verify that FFmpeg is available:
```bash
ffmpeg -version
```

---

### Step 3: Upload or Clone the Bot
In your PythonAnywhere console, navigate to your home directory:
```bash
cd ~
# If using git:
git clone <your-repo-url> yt-bot
cd yt-bot
```
*(Alternatively, you can upload the files as a zip file via the **Files** tab and unzip it with `unzip yt-bot.zip`)*

---

### Step 4: Create a Virtual Environment and Install Dependencies
```bash
cd ~/yt-bot
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 5: Configure `.env`
Create your `.env` file:
```bash
nano .env
```

Add your configuration:
```dotenv
BOT_TOKEN=your_bot_token_from_botfather
ALLOWED_USERS=your_telegram_user_id
MAX_FILE_SIZE_MB=50
```

> 💡 **How to find your Telegram User ID:**
> Send a message to [@userinfobot](https://t.me/userinfobot) on Telegram. It will reply with your numeric ID (e.g. `123456789`). Adding this to `ALLOWED_USERS` ensures only you can use the bot!

Save and exit in nano: press `Ctrl + O`, then `Enter`, then `Ctrl + X`.

---

### Step 6: Test Run the Bot
Test run the bot manually in the console:
```bash
python main.py
```
You should see:
```text
Starting YouTube Downloader Telegram Bot...
Bot running in PRIVATE mode. Allowed users: {123456789}
```
Open Telegram, send `/start` and test a YouTube link to ensure it functions.

---

### Step 7: Run 24/7 (Always-on Task)
If you have a paid PythonAnywhere account:
1. Go to the **Tasks** tab on the PythonAnywhere dashboard.
2. In the **Always-on tasks** section, set the command:
   ```bash
   /home/<your-username>/yt-bot/.venv/bin/python /home/<your-username>/yt-bot/main.py
   ```
   *(Replace `<your-username>` with your actual PythonAnywhere username)*
3. Click **Create**. PythonAnywhere will start the bot process and keep it running continuously in the background!
