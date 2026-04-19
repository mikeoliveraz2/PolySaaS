# PolySaaS Peers Adapter — Render / generic Docker (Mattermost outgoing → Django proxy, phase 1).
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY peers_adapter ./peers_adapter

EXPOSE 8000

# Render sets PORT; default 8000 for local runs.
CMD ["sh", "-c", "exec uvicorn peers_adapter.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
