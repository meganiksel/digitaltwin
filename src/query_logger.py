#!/usr/bin/env python3
"""
JSONL-логгер пользовательских запросов к RAG-боту (Задание 7).

Каждая запись пишется одной строкой в logs/queries.jsonl:
    {
      "ts": "2025-05-31T07:00:00Z",
      "query": "...",
      "chunks_found": 3,
      "answer_length": 142,
      "is_successful": true,
      "sources": ["characters/harry-potter.txt", ...],
      "safety_triggered": ["injection:..."]
    }
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_LOG_PATH = Path(os.getenv("QUERY_LOG_PATH", "logs/queries.jsonl"))

# Маркеры «честного отказа» — используются для флага is_successful.
_UNKNOWN_MARKERS = (
    "я не знаю",
    "не знаю",
    "i don't know",
    "недостаточно информации",
    "не могу дать",
)


def is_unknown_answer(answer: str) -> bool:
    a = (answer or "").lower()
    return any(m in a for m in _UNKNOWN_MARKERS)


def log_query(
    query: str,
    answer: str,
    sources: List[str],
    distances: List[float],
    safety_triggered: Optional[List[str]] = None,
    log_path: Path = DEFAULT_LOG_PATH,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Записать запрос в JSONL-лог. Возвращает записанную строку."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    successful = bool(sources) and not is_unknown_answer(answer) and len(answer) > 20

    record: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "query": query,
        "chunks_found": len(sources),
        "answer_length": len(answer or ""),
        "is_successful": successful,
        "sources": sources,
        "distances": [float(d) for d in distances],
        "safety_triggered": safety_triggered or [],
    }
    if extra:
        record.update(extra)

    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record
