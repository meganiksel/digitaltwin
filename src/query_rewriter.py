#!/usr/bin/env python3
"""Query rewriting: подмена «оригинальной» лексики Harry Potter (EN/RU)
на актуальные термины KB (QuantumForge) перед поиском в индексе.

Зачем: knowledge_base уже переведена `replace_terms.py`, но имена в
исходниках встречаются в разных формах (Harry / Harry Potter / Harry James
Potter). В индексе они отражены как Xander / Xander Thornfield. Если
пользователь спрашивает «Кто такой Гарри Поттер?», прямой match по индексу
не сработает. Этот модуль до поиска переписывает запрос, заменяя алиасы
на канонические формы из KB.

KB и индекс не меняются — это лёгкий слой на стороне запроса.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

ALIASES_PATH = os.getenv(
    "QUERY_ALIASES_PATH", "knowledge_base/query_aliases.json"
)


def _is_cyrillic(s: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", s))


def _load_aliases(path: str) -> Dict[str, str]:
    """Уплощает JSON с категориями в один словарь {alias: canonical}.

    Сортировка применяется на этапе матчинга (от длинных к коротким).
    """
    p = Path(path)
    if not p.exists():
        logger.warning("Query aliases file not found: %s", path)
        return {}
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    flat: Dict[str, str] = {}
    for key, val in data.items():
        if key.startswith("_"):
            continue
        if isinstance(val, dict):
            flat.update(val)
    logger.info("Loaded %d query aliases from %s", len(flat), path)
    return flat


_aliases_cache: Dict[str, str] | None = None


def get_aliases() -> Dict[str, str]:
    global _aliases_cache
    if _aliases_cache is None:
        _aliases_cache = _load_aliases(ALIASES_PATH)
    return _aliases_cache


def rewrite_query(query: str) -> Tuple[str, Dict[str, str]]:
    """Возвращает (переписанный_запрос, применённые_замены).

    Поведение:
    - сортируем алиасы от длинных к коротким (защита от частичных матчей);
    - для кириллических алиасов используем границы по non-letter (\\W),
      т. к. `\\b` в Python regex для кириллицы работает корректно только при
      re.UNICODE (включён по умолчанию в Py3), но мы дополнительно явно
      указываем re.IGNORECASE;
    - replacement подставляется как литерал (re.escape не нужен — это
      просто строка с именами), но защищаем от случайных backreference-
      символов через lambda.
    """
    aliases = get_aliases()
    if not aliases or not query:
        return query, {}

    sorted_aliases = sorted(aliases.items(), key=lambda kv: len(kv[0]), reverse=True)

    applied: Dict[str, str] = {}
    rewritten = query
    for original, replacement in sorted_aliases:
        pattern = re.compile(
            r"(?<!\w)" + re.escape(original) + r"(?!\w)",
            flags=re.IGNORECASE,
        )
        new_text, n = pattern.subn(lambda _m, r=replacement: r, rewritten)
        if n > 0:
            applied[original] = replacement
            rewritten = new_text

    return rewritten, applied


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tests = [
        "Кто такой Гарри Поттер?",
        "Who is Harry Potter?",
        "Что такое Хогвартс?",
        "Какие зелья знает Гермиона?",
        "Расскажи про Voldemort",
        "Что такое патронус и магия?",
    ]
    for q in tests:
        rew, apl = rewrite_query(q)
        print(f"[in ] {q}")
        print(f"[out] {rew}")
        print(f"[map] {apl}")
        print()
