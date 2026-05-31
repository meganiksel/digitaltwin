# DigitalTwin RAG Bot

## Архитектура

```
User → Telegram / HTTP API → RAGCore.query()
                                │
                                ├─ encode (SentenceTransformer)
                                ├─ search FAISS top-K
                                ├─ safety.filter_chunks  (Задание 5)
                                ├─ build prompt (few-shot + CoT + system-guard)
                                ├─ LLM (Ollama / OpenAI / mock)
                                ├─ safety.sanitize_answer
                                └─ log → logs/queries.jsonl
```

Диаграммы:
* [`docs/diagrams/rag_query_sequence.puml`](docs/diagrams/rag_query_sequence.puml:1) — sequence-диаграмма запроса (Задание 7).
* [`docs/diagrams/update_pipeline.puml`](docs/diagrams/update_pipeline.puml:1) — конвейер обновления индекса (Задание 6).

---

## Быстрый старт (локально)

```bash
# 1. Установка
make venv install

# 2. (Опционально) пересборка БЗ из сырых данных
make kb

# 3. Сборка векторного индекса
make index

# 4. Запуск Ollama (на хосте)
ollama serve &
ollama pull gpt-oss:20b      # или другую модель

# 5. Старт API
make run-api                 # http://localhost:8000

# 6. (Опционально) Telegram-бот
export TELEGRAM_BOT_TOKEN=...
make run-bot
```

Проверка пайплайна:
```bash
make test-rag                # python -m src.rag_core
make eval                    # прогон golden-set
make safety-test             # демонстрация защиты от инъекций
```

---

## Запуск через Docker Compose

```bash
cp .env.example .env         # отредактировать токены/модели
docker compose up -d ollama bot-api                  # API + LLM
docker compose --profile telegram up -d telegram-bot # Telegram
docker compose --profile updater  up -d updater      # авто-обновление БЗ
```

Сервисы из [`docker-compose.yml`](docker-compose.yml:1):

| Сервис | Профиль | Что делает |
|--------|---------|-----------|
| `ollama` | default | Локальная LLM, порт `11434` |
| `bot-api` | default | FastAPI на `:8000` |
| `telegram-bot` | `telegram` | Telegram-бот (aiogram 3) |
| `updater` | `updater` | Запускает `scripts/update_index.py` ежедневно в 06:00 |

---

## Переменные окружения

См. полный список в [`.env.example`](.env.example:1). Главные:

| Переменная | По умолчанию | Назначение |
|------------|--------------|-----------|
| `LLM_PROVIDER` | `mock` | `ollama` / `openai` / `mock` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL Ollama |
| `OLLAMA_MODEL` | `gpt-oss:20b` | Имя модели Ollama |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | — | Если используется OpenAI |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Двуязычная модель |
| `FAISS_INDEX_PATH` | `vector_index/faiss_index.bin` | Путь к FAISS |
| `FAISS_CHUNKS_PATH` | `vector_index/chunks.pkl` | Путь к чанкам |
| `RAG_TOP_K` | `3` | Сколько чанков подмешивать |
| `SAFETY_ENABLED` | `true` | Защита от prompt-injection |
| `CHUNK_SIZE`/`CHUNK_OVERLAP` | `500` / `50` | Для пересборки индекса |
| `TELEGRAM_BOT_TOKEN` | — | Токен Telegram-бота |
| `QUERY_LOG_PATH` | `logs/queries.jsonl` | JSONL-лог запросов |

---

## Безопасность

База знаний намеренно содержит «злонамеренный» документ
[`knowledge_base/internal/security_note.txt`](knowledge_base/internal/security_note.txt:1)
с prompt-injection и фейковыми секретами. Запустите:

```bash
make safety-test
```

В результате (`logs/safety_demo.jsonl`) виден реальный эффект защиты:

* без защиты модель **может** процитировать `swordfish` из контекста — это утечка;
* с защитой чанк отбрасывается (`safety_triggered: ["dropped:malicious_chunk"]`),
  ответ не содержит секрета.

В последнем прогоне: 5/5 атак заблокировано, утечка с защитой — 0.

---

## Аналитика и метрики

```bash
make eval         # прогоняет scripts/golden_questions.jsonl
```

Скрипт [`scripts/evaluate.py`](scripts/evaluate.py:1) делит вопросы на:

* `known` — бот **должен** ответить (есть в БЗ);
* `missing` — бот **должен** сказать «Я не знаю» (нет в БЗ либо сущность
  удалена для теста «слепых пятен», см. [`docs/removed_entities.md`](docs/removed_entities.md:1)).

Пример результата (Ollama `gpt-oss:20b`, эмбеддинги
`paraphrase-multilingual-MiniLM-L12-v2`):

```
Категория        Всего    Прошли    Доля
known                8         4    50.0%
missing              7         7   100.0%
OVERALL             15        11    73.3%
```

Логи:
* `logs/queries.jsonl` — каждый запрос (для аналитики покрытия в проде);
* `logs/evaluation.jsonl` — результаты прогона golden-set;
* `logs/safety_demo.jsonl` — результаты демо защиты;
* `logs/update.log` — события обновления индекса.

---

## Структура проекта

```
.
├── docs/
│   ├── diagrams/                 # PlantUML
│   ├── removed_entities.md       # «слепые пятна»
│   └── task*_research.md
├── knowledge_base/               # текущая БЗ (после удалений)
├── knowledge_base_raw/           # исходная БЗ
├── scripts/
│   ├── create_vector_index.py    # пересборка индекса
│   ├── update_index.py           # инкрементальное обновление
│   ├── evaluate.py               # Задание 7
│   ├── safety_demo.py            # Задание 5
│   └── golden_questions.jsonl
├── src/
│   ├── api.py                    # FastAPI
│   ├── telegram_bot.py           # aiogram 3
│   ├── rag_core.py               # ядро RAG
│   ├── llm_providers.py          # Ollama / OpenAI / mock
│   ├── safety.py                 # защита от prompt-injection
│   └── query_logger.py           # JSONL-логирование
├── vector_index/                 # FAISS + chunks.pkl + state
├── logs/                         # рантайм-логи
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── Makefile
├── Project_template.md           # отчёт по 7 заданиям
└── README.md
```

---

## Make-таргеты

| Команда | Что делает |
|---------|-----------|
| `make venv install` | Создать venv и установить зависимости |
| `make kb` | Сборка `knowledge_base/` из сырых данных |
| `make index` | Полная пересборка FAISS-индекса |
| `make update` | Инкрементальное обновление по дельте файлов |
| `make run-api` / `make run-bot` | Старт FastAPI / Telegram |
| `make test-rag` | Прогон `python -m src.rag_core` (4 вопроса) |
| `make eval` | Прогон golden-set |
| `make safety-test` | Демонстрация защиты от prompt-injection |
| `make docker-build` / `docker-up` / `docker-down` | Управление Compose |
| `make clean-logs` | Очистка `logs/` |
