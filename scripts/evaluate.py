#!/usr/bin/env python3
"""
Evaluate RAG bot against a golden set of questions (Задание 7).

JSONL формат входа (scripts/golden_questions.jsonl):
    {"question": "...", "category": "known|missing", "expected_keywords": [...]}

Метрики:
    * known.success_rate   — доля вопросов, на которые бот дал содержательный
                             ответ (is_successful=True), содержащий хотя бы
                             один ожидаемый ключ.
    * missing.refusal_rate — доля вопросов, на которые бот честно ответил
                             «Я не знаю» (is_unknown_answer == True).
    * overall — общий % пройденных кейсов.

Выходы:
    * logs/evaluation.jsonl — построчные результаты каждого вопроса.
    * stdout               — итоговая таблица.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from query_logger import is_unknown_answer  # noqa: E402
from rag_core import get_rag_core  # noqa: E402

DEFAULT_GOLDEN = ROOT / "scripts" / "golden_questions.jsonl"
DEFAULT_OUT = ROOT / "logs" / "evaluation.jsonl"


def load_golden(path: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            items.append(json.loads(line))
    return items


def evaluate_one(rag, item: Dict[str, Any]) -> Dict[str, Any]:
    q = item["question"]
    category = item.get("category", "known")
    expected = [k.lower() for k in item.get("expected_keywords", [])]

    res = rag.query(q)
    answer = res["answer"]
    answer_lower = answer.lower()

    unknown = is_unknown_answer(answer)

    if category == "known":
        keywords_hit = [k for k in expected if k in answer_lower]
        passed = (not unknown) and (not expected or bool(keywords_hit))
    else:  # missing
        keywords_hit = []
        passed = unknown

    return {
        "question": q,
        "category": category,
        "answer": answer,
        "is_unknown": unknown,
        "expected_keywords": expected,
        "keywords_hit": keywords_hit,
        "passed": passed,
        "sources": res["sources"],
        "distances": res["distances"],
        "llm_provider": res["llm_provider"],
        "safety_triggered": res["safety_triggered"],
    }


def write_results(out_path: Path, results: List[Dict[str, Any]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with out_path.open("a", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps({"ts": ts, **r}, ensure_ascii=False) + "\n")


def print_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r)

    print("\n" + "=" * 72)
    print(f"{'Категория':<14}{'Всего':>8}{'Прошли':>10}{'Доля':>10}")
    print("-" * 72)

    summary: Dict[str, Any] = {"by_category": {}}
    for cat, items in by_cat.items():
        total = len(items)
        passed = sum(1 for x in items if x["passed"])
        ratio = passed / total if total else 0.0
        summary["by_category"][cat] = {
            "total": total,
            "passed": passed,
            "ratio": ratio,
        }
        print(f"{cat:<14}{total:>8}{passed:>10}{ratio * 100:>9.1f}%")

    total = len(results)
    total_passed = sum(1 for r in results if r["passed"])
    overall = total_passed / total if total else 0.0
    summary["overall"] = {"total": total, "passed": total_passed, "ratio": overall}

    print("-" * 72)
    print(f"{'OVERALL':<14}{total:>8}{total_passed:>10}{overall * 100:>9.1f}%")
    print("=" * 72)

    failed = [r for r in results if not r["passed"]]
    if failed:
        print("\n[!] Не прошли:")
        for r in failed:
            print(f"  - [{r['category']}] {r['question']}")
            print(f"      answer: {r['answer'][:120]}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate RAG bot")
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    if not args.golden.exists():
        print(f"Golden file not found: {args.golden}", file=sys.stderr)
        return 2

    items = load_golden(args.golden)
    print(f"Загружено вопросов: {len(items)}")

    rag = get_rag_core()
    print(f"LLM-провайдер: {rag.llm.name}")
    print(f"Embedding-модель: {rag.embedding_model_name}")
    print(f"Чанков в индексе: {len(rag.chunks)}")

    results: List[Dict[str, Any]] = []
    for i, item in enumerate(items, 1):
        print(f"\n[{i}/{len(items)}] {item['question']} ({item.get('category')})")
        r = evaluate_one(rag, item)
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  -> {status} | {r['answer'][:140]}")
        results.append(r)

    write_results(args.out, results)
    summary = print_summary(results)
    print(f"\nЛог сохранён в {args.out}")
    print(f"Лог запросов:    {os.getenv('QUERY_LOG_PATH', 'logs/queries.jsonl')}")

    return 0 if summary["overall"]["ratio"] >= 0.7 else 1


if __name__ == "__main__":
    raise SystemExit(main())
