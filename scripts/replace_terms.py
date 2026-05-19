#!/usr/bin/env python3
"""
Скрипт для замены терминов в текстах базы знаний.
Заменяет оригинальные термины вселенной Гарри Поттера на вымышленные.
"""

import json
import re
from pathlib import Path
from typing import Dict


def load_terms_map(file_path: str) -> Dict[str, str]:
    """Загружает словарь замен из JSON файла."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Объединяем все категории в один словарь
    terms_map = {}
    for category, replacements in data.items():
        terms_map.update(replacements)
    
    return terms_map


def replace_terms_in_text(text: str, terms_map: Dict[str, str]) -> str:
    """
    Заменяет все термины в тексте согласно словарю замен.
    
    Args:
        text: Исходный текст
        terms_map: Словарь замен {оригинал: замена}
    
    Returns:
        Текст с заменёнными терминами
    """
    # Сортируем термины по длине (от длинных к коротким)
    # чтобы избежать частичных замен (например, "Harry Potter" → "Xander Thornfield",
    # а не "Harry" → "Xander" и "Potter" → "Thornfield")
    sorted_terms = sorted(terms_map.items(), key=lambda x: len(x[0]), reverse=True)
    
    result = text
    for original, replacement in sorted_terms:
        # Используем регулярные выражения для замены с учётом границ слов
        # \b означает границу слова
        pattern = r'\b' + re.escape(original) + r'\b'
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


def process_file(input_path: Path, output_path: Path, terms_map: Dict[str, str]) -> None:
    """
    Обрабатывает один файл: заменяет термины и сохраняет результат.
    
    Args:
        input_path: Путь к исходному файлу
        output_path: Путь к выходному файлу
        terms_map: Словарь замен
    """
    print(f"Обработка файла: {input_path}")
    
    # Читаем исходный файл
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Заменяем термины
    replaced_text = replace_terms_in_text(text, terms_map)
    
    # Создаём директорию для выходного файла, если нужно
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Сохраняем результат
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(replaced_text)
    
    print(f"Сохранено: {output_path}")


def main():
    """Главная функция скрипта."""
    # Пути к файлам
    base_dir = Path(__file__).parent.parent
    terms_map_path = base_dir / "knowledge_base" / "terms_map.json"
    
    # Директории с исходными и обработанными файлами
    input_dir = base_dir / "knowledge_base_raw"
    output_dir = base_dir / "knowledge_base"
    
    # Загружаем словарь замен
    print("Загрузка словаря замен...")
    terms_map = load_terms_map(terms_map_path)
    print(f"Загружено {len(terms_map)} замен")
    
    # Если директория с исходными файлами существует, обрабатываем её
    if input_dir.exists():
        print(f"\nОбработка файлов из {input_dir}...")
        
        # Обрабатываем все текстовые файлы
        for input_file in input_dir.rglob("*.txt"):
            # Вычисляем относительный путь
            rel_path = input_file.relative_to(input_dir)
            output_file = output_dir / rel_path
            
            process_file(input_file, output_file, terms_map)
    else:
        print(f"\nДиректория {input_dir} не найдена.")
        print("Создайте директорию knowledge_base_raw и поместите туда исходные файлы.")
        print("\nПример использования:")
        print("  knowledge_base_raw/")
        print("    characters/")
        print("      harry_potter.txt")
        print("      hermione_granger.txt")
        print("    locations/")
        print("      hogwarts.txt")
        print("      diagon_alley.txt")
    
    print("\nГотово!")


if __name__ == "__main__":
    main()
