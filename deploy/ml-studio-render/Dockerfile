# Machine Learning Studio — own image so Core stays slim; add numpy/torch/etc. in requirements.txt as needed.
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ml_studio_serve ./ml_studio_serve

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn ml_studio_serve.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
