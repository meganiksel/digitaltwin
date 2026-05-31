#!/usr/bin/env python3
"""
Абстракция LLM-провайдеров для RAG-бота.

Поддерживаются:
  * OllamaProvider  — локальный сервер Ollama (рекомендуется, см. Задание 1).
  * OpenAIProvider  — облачный fallback при наличии OPENAI_API_KEY.
  * MockProvider    — детерминированная заглушка (если LLM недоступна).

Выбор провайдера управляется переменной окружения LLM_PROVIDER:
    LLM_PROVIDER=ollama|openai|mock   (по умолчанию ollama, с fallback на mock)
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Базовый интерфейс LLM-провайдера."""

    name: str = "base"

    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Сгенерировать ответ по prompt-у."""

    def healthcheck(self) -> bool:  # pragma: no cover - чисто диагностический хук
        return True


class OllamaProvider(BaseLLMProvider):
    """Локальный LLM через Ollama (http://ollama:11434/api/generate)."""

    name = "ollama"

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120,
        temperature: float = 0.2,
    ):
        self.host = (host or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
        self.timeout = timeout
        self.temperature = temperature

    def healthcheck(self) -> bool:
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=3)
            return r.ok
        except requests.RequestException:
            return False

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if system:
            payload["system"] = system

        resp = requests.post(
            f"{self.host}/api/generate", json=payload, timeout=self.timeout
        )
        resp.raise_for_status()
        data = resp.json()
        return (data.get("response") or "").strip()


class OpenAIProvider(BaseLLMProvider):
    """Облачный fallback. Использует chat-completions REST API напрямую."""

    name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = (
            base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        ).rstrip("/")
        self.timeout = timeout

    def healthcheck(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self.model, "messages": messages, "temperature": 0.2},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


class MockProvider(BaseLLMProvider):
    """Детерминированная заглушка для CI/локальной отладки без LLM."""

    name = "mock"

    UNKNOWN_RESPONSE = (
        "Я не знаю. В предоставленной базе знаний нет информации, "
        "достаточной для ответа на этот вопрос."
    )

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        marker = "Контекст:"
        if marker not in prompt:
            return self.UNKNOWN_RESPONSE

        context = prompt.split(marker, 1)[1]
        if "Вопрос:" in context:
            context = context.split("Вопрос:", 1)[0]

        snippet = context.strip()
        if not snippet or len(snippet) < 30:
            return self.UNKNOWN_RESPONSE

        head = snippet[:600].rsplit(".", 1)[0]
        return (
            "Размышления:\n"
            "1. Извлёк релевантные фрагменты из базы знаний.\n"
            "2. Сформирую ответ строго по ним.\n\n"
            f"Ответ: {head.strip()}."
        )


def get_llm_provider(name: Optional[str] = None) -> BaseLLMProvider:
    """Возвращает провайдера по env LLM_PROVIDER. Фолбэк на mock, если основной недоступен."""
    name = (name or os.getenv("LLM_PROVIDER", "ollama")).lower().strip()

    if name == "openai":
        prov = OpenAIProvider()
        if prov.healthcheck():
            return prov
        logger.warning("OpenAI provider unavailable, falling back to mock")
        return MockProvider()

    if name == "mock":
        return MockProvider()

    prov = OllamaProvider()
    if prov.healthcheck():
        return prov
    logger.warning(
        "Ollama provider unavailable at %s, falling back to mock", prov.host
    )
    return MockProvider()


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    p = get_llm_provider()
    print(f"provider: {p.name}")
    print(p.generate("Контекст:\nЗелье Felix Felicis приносит удачу.\nВопрос: что приносит удачу?\nОтвет:"))
