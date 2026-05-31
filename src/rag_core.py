#!/usr/bin/env python3
"""RAG Core: FAISS retrieval + few-shot/CoT prompting + LLM (Задание 4).

LLM-провайдер выбирается через `llm_providers`, защита от prompt-injection —
через `safety` (Задание 5), логирование запросов — через `query_logger`
(Задание 7).
"""

from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import faiss
from sentence_transformers import SentenceTransformer

try:
    from .llm_providers import BaseLLMProvider, get_llm_provider
    from .safety import (
        SAFETY_ENABLED_DEFAULT,
        SYSTEM_PROMPT_GUARD,
        filter_chunks,
        sanitize_answer,
    )
    from .query_logger import log_query
except ImportError:
    from llm_providers import BaseLLMProvider, get_llm_provider  # type: ignore
    from safety import (  # type: ignore
        SAFETY_ENABLED_DEFAULT,
        SYSTEM_PROMPT_GUARD,
        filter_chunks,
        sanitize_answer,
    )
    from query_logger import log_query  # type: ignore

logger = logging.getLogger(__name__)

INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "vector_index/faiss_index.bin")
CHUNKS_PATH = os.getenv("FAISS_CHUNKS_PATH", "vector_index/chunks.pkl")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
TOP_K = int(os.getenv("RAG_TOP_K", "3"))


class RAGCore:
    """Pipeline: encode → search FAISS → build prompt → LLM → answer."""

    def __init__(
        self,
        llm: Optional[BaseLLMProvider] = None,
        index_path: str = INDEX_PATH,
        chunks_path: str = CHUNKS_PATH,
        embedding_model: str = EMBEDDING_MODEL,
    ):
        self.index_path = index_path
        self.chunks_path = chunks_path
        self.embedding_model_name = embedding_model
        self.llm: BaseLLMProvider = llm or get_llm_provider()
        logger.info("Using LLM provider: %s", self.llm.name)
        self._load_resources()

    def _load_resources(self) -> None:
        if not Path(self.index_path).exists():
            raise FileNotFoundError(
                f"FAISS index not found at {self.index_path}. "
                "Run `python scripts/create_vector_index.py` first."
            )
        if not Path(self.chunks_path).exists():
            raise FileNotFoundError(f"Chunks file not found at {self.chunks_path}")

        self.index = faiss.read_index(self.index_path)
        with open(self.chunks_path, "rb") as f:
            self.chunks: List[Dict[str, Any]] = pickle.load(f)
        self.model = SentenceTransformer(self.embedding_model_name)

    def search(self, query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
        query_embedding = self.model.encode([query]).astype("float32")
        distances, indices = self.index.search(query_embedding, k=top_k)

        results: List[Dict[str, Any]] = []
        for dist, idx in zip(distances[0], indices[0]):
            if 0 <= idx < len(self.chunks):
                chunk = dict(self.chunks[idx])
                chunk["distance"] = float(dist)
                results.append(chunk)
        return results

    @staticmethod
    def format_context(results: List[Dict[str, Any]]) -> str:
        parts: List[str] = []
        for i, r in enumerate(results, 1):
            parts.append(
                f"[Источник {i}: {r.get('source', '?')} | "
                f"категория: {r.get('category', '?')}]"
            )
            parts.append(r.get("text", "").strip())
            parts.append("---")
        return "\n".join(parts).strip()

    def _build_prompt(
        self,
        query: str,
        context: str,
        use_few_shot: bool,
        use_cot: bool,
    ) -> str:
        parts: List[str] = []

        if use_cot:
            parts.append(
                "Думай пошагово: сначала перечисли релевантные факты из контекста, "
                "потом сформулируй итоговый ответ. Если фактов недостаточно — "
                "ответь честно «Я не знаю».\n"
            )

        if use_few_shot:
            parts.append("Пример 1.")
            parts.append("Контекст: Зелье Felix Felicis приносит удачу выпившему.")
            parts.append("Вопрос: Какое зелье приносит удачу?")
            parts.append(
                "Размышления: в контексте упомянуто зелье Felix Felicis, "
                "которое описано как приносящее удачу.\n"
                "Ответ: Felix Felicis.\n"
            )
            parts.append("Пример 2.")
            parts.append("Контекст: (нет упоминаний о столице планеты Ти'лора).")
            parts.append("Вопрос: Как называется столица планеты Ти'лора?")
            parts.append(
                "Размышления: в контексте нет данных о такой планете.\n"
                "Ответ: Я не знаю.\n"
            )

        parts.append("Контекст:")
        parts.append(context if context else "(пусто)")
        parts.append("")
        parts.append(f"Вопрос: {query}")
        parts.append("Ответ:")
        return "\n".join(parts)

    def query(
        self,
        user_query: str,
        top_k: int = TOP_K,
        use_few_shot: bool = True,
        use_cot: bool = True,
        safety_enabled: Optional[bool] = None,
        log: bool = True,
    ) -> Dict[str, Any]:
        if safety_enabled is None:
            safety_enabled = SAFETY_ENABLED_DEFAULT

        raw_results = self.search(user_query, top_k=top_k)
        results = filter_chunks(raw_results, enabled=safety_enabled)

        context = self.format_context(results)
        prompt = self._build_prompt(user_query, context, use_few_shot, use_cot)
        system = SYSTEM_PROMPT_GUARD if safety_enabled else None

        try:
            answer = self.llm.generate(prompt, system=system)
        except Exception as exc:  # pragma: no cover
            logger.exception("LLM generation failed")
            answer = (
                "Произошла ошибка при обращении к языковой модели. "
                f"Подробности: {exc}"
            )

        answer = sanitize_answer(answer, enabled=safety_enabled)

        triggered: List[str] = []
        for r in results:
            triggered.extend(r.get("safety_triggered", []) or [])
            if r.get("safety_dropped"):
                triggered.append("dropped:malicious_chunk")

        result = {
            "answer": answer,
            "context": context,
            "sources": [r.get("source", "?") for r in results],
            "distances": [r.get("distance", 0.0) for r in results],
            "query": user_query,
            "safety_triggered": triggered,
            "llm_provider": self.llm.name,
        }

        if log:
            try:
                log_query(
                    query=user_query,
                    answer=answer,
                    sources=result["sources"],
                    distances=result["distances"],
                    safety_triggered=triggered,
                    extra={"llm_provider": self.llm.name},
                )
            except Exception:  # pragma: no cover
                logger.exception("Failed to log query")

        return result


_rag_core_instance: Optional[RAGCore] = None


def get_rag_core() -> RAGCore:
    """Ленивый singleton — импорт модуля не падает, пока индекс не нужен."""
    global _rag_core_instance
    if _rag_core_instance is None:
        _rag_core_instance = RAGCore()
    return _rag_core_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rag = get_rag_core()
    for q in [
        "Кто такой Гарри Поттер?",
        "Какое зелье приносит удачу?",
        "Что такое патронус?",
        "Как называется столица планеты Ти'лора?",  # ожидаем «не знаю»
    ]:
        print("\n=== Q:", q)
        res = rag.query(q)
        print("A:", res["answer"])
        print("sources:", res["sources"])
