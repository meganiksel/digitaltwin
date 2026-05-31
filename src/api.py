#!/usr/bin/env python3
"""REST API для RAG-бота на FastAPI (Задание 4)."""

from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag_core import get_rag_core

app = FastAPI(
    title="RAG Bot API",
    description="API для RAG-бота по вселенной Гарри Поттера",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str = Field(..., description="Текстовый запрос пользователя", min_length=1)
    use_few_shot: bool = Field(True, description="Использовать few-shot prompting")
    use_cot: bool = Field(True, description="Использовать Chain-of-Thought")
    top_k: Optional[int] = Field(3, description="Количество релевантных чанков", ge=1, le=10)


class QueryResponse(BaseModel):
    answer: str
    context: str
    sources: List[str]
    distances: List[float]
    query: str


class HealthResponse(BaseModel):
    status: str
    message: str


@app.get("/", response_model=HealthResponse)
async def root():
    return {"status": "ok", "message": "RAG Bot API работает"}


@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "healthy", "message": "API готов к работе"}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        rag = get_rag_core()
        result = rag.query(
            user_query=request.query,
            use_few_shot=request.use_few_shot,
            use_cot=request.use_cot,
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info")
async def info():
    return {
        "name": "RAG Bot API",
        "version": "1.0.0",
        "description": "API для RAG-бота по вселенной Гарри Поттера",
        "features": [
            "Векторный поиск по базе знаний",
            "Few-shot prompting",
            "Chain-of-Thought",
            "REST API",
        ],
    }


def main():
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
