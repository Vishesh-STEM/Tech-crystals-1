# Vidyalaya AI - FastAPI backend
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Optional AI extras (ChromaDB / sentence-transformers). Uncomment to include:
# COPY backend/requirements-ai.txt /app/requirements-ai.txt
# RUN pip install --no-cache-dir -r requirements-ai.txt

COPY backend /app
COPY database /app/database

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
