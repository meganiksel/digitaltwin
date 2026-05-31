#!/usr/bin/env python3
"""Построение FAISS-индекса из knowledge_base/ (Задание 3).

Sentence-Transformers → эмбеддинги → FAISS IndexFlatL2.
"""

import json
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
INDEX_PATH = os.getenv("VECTOR_INDEX_DIR", "vector_index")
KNOWLEDGE_BASE_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base")


def load_text_files(kb_path: str) -> List[Dict[str, Any]]:
    documents = []
    kb_dir = Path(kb_path)
    print(f"Загрузка файлов из {kb_path}...")

    for txt_file in kb_dir.rglob("*.txt"):
        if txt_file.name == "terms_map.json":
            continue
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                content = f.read()
            category = txt_file.parent.name
            if category == kb_dir.name:
                category = "root"
            documents.append({
                "path": str(txt_file.relative_to(kb_dir)),
                "category": category,
                "content": content,
                "filename": txt_file.name,
            })
        except Exception as e:
            print(f"Ошибка при чтении файла {txt_file}: {e}")

    print(f"Загружено {len(documents)} документов")
    return documents


def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Чанкование по предложениям с перекрытием. Размер — в «токенах» (~4 символа)."""
    if not text:
        return []

    sentences = text.split('. ')
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        sentence_length = len(sentence) // 4

        if current_length + sentence_length > chunk_size and current_chunk:
            chunks.append('. '.join(current_chunk) + '.')

            overlap_sentences: List[str] = []
            overlap_length = 0
            for sent in reversed(current_chunk):
                sent_length = len(sent) // 4
                if overlap_length + sent_length <= overlap:
                    overlap_sentences.insert(0, sent)
                    overlap_length += sent_length
                else:
                    break
            current_chunk = overlap_sentences
            current_length = overlap_length

        current_chunk.append(sentence)
        current_length += sentence_length

    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')

    return chunks


def create_chunks(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    print(f"Разбивка документов на чанки (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    for doc in documents:
        for i, chunk in enumerate(split_text_into_chunks(doc["content"])):
            chunks.append({
                "text": chunk,
                "source": doc["path"],
                "category": doc["category"],
                "filename": doc["filename"],
                "chunk_id": i,
            })
    print(f"Создано {len(chunks)} чанков")
    return chunks


def create_embeddings(chunks: List[Dict[str, Any]], model_name: str = EMBEDDING_MODEL) -> Tuple[np.ndarray, SentenceTransformer]:
    print(f"Загрузка модели эмбеддингов: {model_name}")
    model = SentenceTransformer(model_name)
    print(f"Генерация эмбеддингов для {len(chunks)} чанков...")
    embeddings = model.encode([c["text"] for c in chunks], show_progress_bar=True)
    print(f"Размерность эмбеддингов: {embeddings.shape[1]}")
    return embeddings, model


def create_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    dimension = embeddings.shape[1]
    print(f"Создание FAISS IndexFlatL2 (dim={dimension})...")
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype('float32'))
    print(f"Индекс создан, добавлено {index.ntotal} векторов")
    return index


def save_index(index: faiss.Index, chunks: List[Dict[str, Any]], model: SentenceTransformer, output_path: str = INDEX_PATH):
    output_dir = Path(output_path)
    output_dir.mkdir(exist_ok=True)

    index_path = output_dir / "faiss_index.bin"
    faiss.write_index(index, str(index_path))
    print(f"Индекс сохранен: {index_path}")

    chunks_path = output_dir / "chunks.pkl"
    with open(chunks_path, "wb") as f:
        pickle.dump(chunks, f)
    print(f"Чанки сохранены: {chunks_path}")

    model_info = {
        "model_name": EMBEDDING_MODEL,
        "dimension": index.d,
        "total_vectors": index.ntotal,
        "total_chunks": len(chunks),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }
    info_path = output_dir / "index_info.json"
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(model_info, f, indent=2, ensure_ascii=False)
    print(f"Информация об индексе сохранена: {info_path}")


def test_search(index: faiss.Index, chunks: List[Dict[str, Any]], model: SentenceTransformer, queries: List[str], k: int = 3):
    print("\n" + "=" * 60)
    print("Тестирование поиска")
    print("=" * 60)
    for query in queries:
        print(f"\nЗапрос: {query}")
        query_embedding = model.encode([query])
        distances, indices = index.search(query_embedding.astype('float32'), k)
        print(f"Топ-{k} результатов:")
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(chunks):
                chunk = chunks[idx]
                print(f"\n  {i+1}. Расстояние: {dist:.4f}")
                print(f"     Источник: {chunk['source']}")
                print(f"     Категория: {chunk['category']}")
                print(f"     Текст: {chunk['text'][:200]}...")


def main():
    print("=" * 60)
    print("Создание векторного индекса")
    print("=" * 60)

    documents = load_text_files(KNOWLEDGE_BASE_PATH)
    if not documents:
        print("Ошибка: Не найдено документов для обработки")
        return

    chunks = create_chunks(documents)
    embeddings, model = create_embeddings(chunks)
    index = create_faiss_index(embeddings)
    save_index(index, chunks, model, INDEX_PATH)

    test_queries = [
        "Кто такой Гарри Поттер?",
        "Какое зелье приносит удачу?",
        "Какой факультет у Гарри Поттера?",
        "Что такое патронус?",
    ]
    test_search(index, chunks, model, test_queries)

    print("\n" + "=" * 60)
    print("Создание векторного индекса завершено!")
    print("=" * 60)
    print(f"Индекс сохранен в: {INDEX_PATH}/")
    print(f"Всего чанков: {len(chunks)}")
    print(f"Размерность: {embeddings.shape[1]}")


if __name__ == "__main__":
    main()
