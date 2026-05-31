#!/usr/bin/env python3
"""Замена оригинальных терминов Гарри Поттера на термины QuantumForge (Задание 2)."""

import json
import re
from pathlib import Path
from typing import Dict


def load_terms_map(file_path: str) -> Dict[str, str]:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    terms_map: Dict[str, str] = {}
    for _category, replacements in data.items():
        terms_map.update(replacements)
    return terms_map


def replace_terms_in_text(text: str, terms_map: Dict[str, str]) -> str:
    # Сортировка от длинных к коротким защищает от частичных замен
    # ("Harry Potter" целиком, а не "Harry" + "Potter" по отдельности).
    sorted_terms = sorted(terms_map.items(), key=lambda x: len(x[0]), reverse=True)
    result = text
    for original, replacement in sorted_terms:
        pattern = r'\b' + re.escape(original) + r'\b'
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def process_file(input_path: Path, output_path: Path, terms_map: Dict[str, str]) -> None:
    print(f"Обработка файла: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    replaced_text = replace_terms_in_text(text, terms_map)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(replaced_text)
    print(f"Сохранено: {output_path}")


def main():
    base_dir = Path(__file__).parent.parent
    terms_map_path = base_dir / "knowledge_base" / "terms_map.json"
    input_dir = base_dir / "knowledge_base_raw"
    output_dir = base_dir / "knowledge_base"

    print("Загрузка словаря замен...")
    terms_map = load_terms_map(terms_map_path)
    print(f"Загружено {len(terms_map)} замен")

    if input_dir.exists():
        print(f"\nОбработка файлов из {input_dir}...")
        for input_file in input_dir.rglob("*.txt"):
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
