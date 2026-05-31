PY ?= .venv/bin/python
PIP ?= .venv/bin/pip

.PHONY: help venv install kb index update run-api run-bot test-rag eval safety-test docker-build docker-up docker-down clean-logs

help:
	@echo "Доступные цели:"
	@echo "  venv          - создать виртуальное окружение"
	@echo "  install       - установить зависимости"
	@echo "  kb            - скачать базу знаний (PotterDB) и применить подмену терминов"
	@echo "  index         - пересобрать FAISS-индекс"
	@echo "  update        - инкрементальное обновление индекса (Задание 6)"
	@echo "  run-api       - запустить REST API (http://localhost:8000)"
	@echo "  run-bot       - запустить Telegram-бот (нужен TELEGRAM_TOKEN)"
	@echo "  test-rag      - smoke-test пайплайна"
	@echo "  eval          - прогнать golden set (Задание 7)"
	@echo "  safety-test   - 10 запросов: 5 положительных + 5 отказов/фильтра"
	@echo "  docker-build  - собрать docker-образы"
	@echo "  docker-up     - запустить compose (bot-api + ollama)"
	@echo "  docker-down   - остановить compose"
	@echo "  clean-logs    - очистить директорию logs/"

venv:
	python3 -m venv .venv

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

kb:
	$(PY) scripts/download_potterdb.py
	$(PY) scripts/replace_terms.py

index:
	$(PY) scripts/create_vector_index.py

update:
	$(PY) scripts/update_index.py

run-api:
	cd src && ../$(PY) -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload

run-bot:
	$(PY) src/telegram_bot.py

test-rag:
	LLM_PROVIDER=$${LLM_PROVIDER:-ollama} $(PY) src/rag_core.py

eval:
	$(PY) scripts/evaluate.py

safety-test:
	$(PY) scripts/safety_demo.py

docker-build:
	docker compose build

docker-up:
	docker compose up -d ollama bot-api

docker-down:
	docker compose down

clean-logs:
	rm -f logs/*.jsonl logs/*.log
