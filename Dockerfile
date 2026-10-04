FROM python:3.12-slim

# Prevent Python from writing .pyc and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install ffmpeg, nodejs (for yt-dlp JavaScript cipher deciphering), and ca-certificates
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure downloads directory exists
RUN mkdir -p /app/downloads

# Run the bot
CMD ["python", "main.py"]
