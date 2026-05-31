FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

# Системные зависимости (нужны faiss/torch на slim-образе)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Сначала зависимости — для кэширования слоя
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем исходники, скрипты, базу знаний и индекс
COPY src /app/src
COPY scripts /app/scripts
COPY knowledge_base /app/knowledge_base
COPY vector_index /app/vector_index

ENV PYTHONPATH=/app/src \
    FAISS_INDEX_PATH=/app/vector_index/faiss_index.bin \
    FAISS_CHUNKS_PATH=/app/vector_index/chunks.pkl \
    KNOWLEDGE_BASE_PATH=/app/knowledge_base \
    QUERY_LOG_PATH=/app/logs/queries.jsonl

EXPOSE 8000

# По умолчанию запускаем REST API; telegram-бот — отдельным сервисом compose
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "/app/src"]
