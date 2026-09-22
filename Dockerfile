# Volta Newsletter — container for Render / Railway / Fly.io
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    VOLTA_DATA_DIR=/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY main.py .
COPY data/internal ./data/internal

# Ephemeral default; mount a persistent volume at /data in production.
# Without a volume, recommendations/drafts/consent are wiped on every redeploy.
RUN mkdir -p /data/recommendations /data/drafts /data/sends

EXPOSE 8000

# Bind to $PORT so Render/Railway/Fly can inject the listen port.
CMD ["sh", "-c", "uvicorn app.web.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
