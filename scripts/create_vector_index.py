#!/usr/bin/env python3
"""
Скрипт для создания векторного индекса из базы знаний
Использует Sentence-Transformers для эмбеддингов и FAISS для векторного поиска
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Any
import numpy as np

# Импорты для эмбеддингов и FAISS
from sentence_transformers import SentenceTransformer
import faiss

# Конфигурация
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
INDEX_PATH = "vector_index"
KNOWLEDGE_BASE_PATH = "knowledge_base"


def load_text_files(kb_path: str) -> List[Dict[str, Any]]:
    """
    Загружает все текстовые файлы из базы знаний
    """
    documents = []
    kb_dir = Path(kb_path)
    
    print(f"Загрузка файлов из {kb_path}...")
    
    for txt_file in kb_dir.rglob("*.txt"):
        # Пропускаем файл terms_map.json
        if txt_file.name == "terms_map.json":
            continue
            
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Определяем категорию по пути
            category = txt_file.parent.name
            if category == kb_dir.name:
                category = "root"
                
            documents.append({
                "path": str(txt_file.relative_to(kb_dir)),
                "category": category,
                "content": content,
                "filename": txt_file.name
            })
            
        except Exception as e:
            print(f"Ошибка при чтении файла {txt_file}: {e}")
    
    print(f"Загружено {len(documents)} документов")
    return documents


def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Разбивает текст на чанки с перекрытием
    """
    if not text:
        return []
    
    # Разбиваем по предложениям
    sentences = text.split('. ')
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Приблизительная оценка длины в токенах (1 токен ≈ 4 символа для английского)
        sentence_length = len(sentence) // 4
        
        if current_length + sentence_length > chunk_size and current_chunk:
            # Сохраняем текущий чанк
            chunks.append('. '.join(current_chunk) + '.')
            
            # Создаем новый чанк с перекрытием
            overlap_sentences = []
            overlap_length = 0
            
            # Добавляем предложения из конца предыдущего чанка для перекрытия
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
    
    # Добавляем последний чанк
    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')
    
    return chunks


def create_chunks(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Создает чанки из документов
    """
    chunks = []
    
    print(f"Разбивка документов на чанки (размер: {CHUNK_SIZE} токенов, перекрытие: {CHUNK_OVERLAP} токенов)...")
    
    for doc in documents:
        text_chunks = split_text_into_chunks(doc["content"])
        
        for i, chunk in enumerate(text_chunks):
            chunks.append({
                "text": chunk,
                "source": doc["path"],
                "category": doc["category"],
                "filename": doc["filename"],
                "chunk_id": i
            })
    
    print(f"Создано {len(chunks)} чанков")
    return chunks


def create_embeddings(chunks: List[Dict[str, Any]], model_name: str = EMBEDDING_MODEL) -> Tuple[np.ndarray, SentenceTransformer]:
    """
    Создает эмбеддинги для чанков
    """
    print(f"Загрузка модели эмбеддингов: {model_name}")
    model = SentenceTransformer(model_name)
    
    print(f"Генерация эмбеддингов для {len(chunks)} чанков...")
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    print(f"Размерность эмбеддингов: {embeddings.shape[1]}")
    return embeddings, model


def create_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Создает FAISS индекс
    """
    dimension = embeddings.shape[1]
    
    print(f"Создание FAISS индекса (размерность: {dimension})...")
    
    # Используем IndexFlatL2 (L2 расстояние) для точного поиска
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype('float32'))
    
    print(f"Индекс создан, добавлено {index.ntotal} векторов")
    return index


def save_index(index: faiss.Index, chunks: List[Dict[str, Any]], model: SentenceTransformer, output_path: str = INDEX_PATH):
    """
    Сохраняет индекс и метаданные
    """
    output_dir = Path(output_path)
    output_dir.mkdir(exist_ok=True)
    
    # Сохраняем FAISS индекс
    index_path = output_dir / "faiss_index.bin"
    faiss.write_index(index, str(index_path))
    print(f"Индекс сохранен: {index_path}")
    
    # Сохраняем чанки с метаданными
    chunks_path = output_dir / "chunks.pkl"
    with open(chunks_path, "wb") as f:
        pickle.dump(chunks, f)
    print(f"Чанки сохранены: {chunks_path}")
    
    # Сохраняем информацию о модели
    model_info = {
        "model_name": EMBEDDING_MODEL,
        "dimension": index.d,
        "total_vectors": index.ntotal,
        "total_chunks": len(chunks),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP
    }
    
    info_path = output_dir / "index_info.json"
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(model_info, f, indent=2, ensure_ascii=False)
    print(f"Информация об индексе сохранена: {info_path}")


def test_search(index: faiss.Index, chunks: List[Dict[str, Any]], model: SentenceTransformer, queries: List[str], k: int = 3):
    """
    Тестирует поиск по индексу
    """
    print("\n" + "=" * 60)
    print("Тестирование поиска")
    print("=" * 60)
    
    for query in queries:
        print(f"\nЗапрос: {query}")
        
        # Создаем эмбеддинг для запроса
        query_embedding = model.encode([query])
        
        # Ищем ближайшие векторы
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
    """
    Основная функция для создания векторного индекса
    """
    print("=" * 60)
    print("Создание векторного индекса")
    print("=" * 60)
    
    # 1. Загружаем документы
    documents = load_text_files(KNOWLEDGE_BASE_PATH)
    
    if not documents:
        print("Ошибка: Не найдено документов для обработки")
        return
    
    # 2. Разбиваем на чанки
    chunks = create_chunks(documents)
    
    # 3. Создаем эмбеддинги
    embeddings, model = create_embeddings(chunks)
    
    # 4. Создаем FAISS индекс
    index = create_faiss_index(embeddings)
    
    # 5. Сохраняем индекс
    save_index(index, chunks, model, INDEX_PATH)
    
    # 6. Тестируем поиск
    test_queries = [
        "Кто такой Гарри Поттер?",
        "Какое зелье приносит удачу?",
        "Какой факультет у Гарри Поттера?",
        "Что такое патронус?"
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
