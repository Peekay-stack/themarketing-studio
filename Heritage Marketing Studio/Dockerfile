# Heritage Marketing Studio — full stack in one container (backend serves the front end).
FROM python:3.12-slim

# Python block-buffers stdout by default when it isn't a TTY — exactly the case here under uvicorn.
# A real print()-based diagnostic (brandbrief.py's enrich_with_ai() failure log) was added to help
# debug a live export failure, then never showed up anywhere in Render's log stream — the exception
# was real (confirmed by the honest caveat it left in the actual document) but sat in a buffer instead
# of reaching the log tail. Standard, low-risk fix: force unbuffered output for the whole process.
ENV PYTHONUNBUFFERED=1

# System libs: cairo (brand-brief figures), fonts, and Node.js (brand-brief .docx builder).
RUN apt-get update && apt-get install -y --no-install-recommends \
      libcairo2 fonts-dejavu-core curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Python deps
RUN pip install --no-cache-dir -r api/requirements.txt
# Node deps for the brand-brief Word builder
RUN cd api/brief_assets && npm install --no-audit --no-fund

WORKDIR /app/api
EXPOSE 8000
# Respect the platform's $PORT (Render/Railway/Fly set it); default 8000 locally.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
