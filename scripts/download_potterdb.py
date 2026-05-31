#!/usr/bin/env python3
"""Скачивание данных из PotterDB API (https://docs.potterdb.com/) — сырьё для Задания 2."""

import requests
import json
import time
from pathlib import Path
from typing import Dict, Any

BASE_URL = "https://api.potterdb.com/v1"

POPULAR_CHARACTERS = [
    "harry-potter",
    "hermione-granger",
    "ron-weasley",
    "albus-dumbledore",
    "severus-snape",
    "lord-voldemort",
    "draco-malfoy",
    "sirius-black",
    "remus-lupin",
    "rubeus-hagrid",
    "minerva-mcgonagall",
    "neville-longbottom",
    "luna-lovegood",
    "ginny-weasley",
    "fred-weasley",
    "george-weasley",
    "dobby",
    "bellatrix-lestrange",
    "lucius-malfoy",
    "molly-weasley",
    "arthur-weasley",
    "bill-weasley",
    "charlie-weasley",
    "percy-weasley",
    "cedric-diggory",
    "cho-chang",
    "lily-potter",
    "james-potter",
    "peter-pettigrew",
    "narcissa-malfoy"
]

POPULAR_SPELLS = [
    "expelliarmus",
    "expecto-patronum",
    "avada-kedavra",
    "crucio",
    "imperio",
    "lumos",
    "nox",
    "wingardium-leviosa",
    "accio",
    "alohomora",
    "petrificus-totalus",
    "stupefy",
    "protego",
    "riddikulus",
    "sectumsempra",
    "obliviate",
    "reparo",
    "scourgify",
    "incendio",
    "aguamenti"
]

POPULAR_POTIONS = [
    "felix-felicis",
    "polyjuice-potion",
    "veritaserum",
    "amortentia",
    "draught-of-living-death",
    "skele-gro",
    "pepperup-potion",
    "wolfsbane-potion",
    "antidote-to-common-poisons",
    "bezoar"
]


def fetch_character_by_slug(slug: str) -> Dict[str, Any]:
    try:
        url = f"{BASE_URL}/characters/{slug}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get("data")
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке персонажа {slug}: {e}")
        return None


def fetch_spell_by_slug(slug: str) -> Dict[str, Any]:
    try:
        url = f"{BASE_URL}/spells/{slug}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get("data")
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке заклинания {slug}: {e}")
        return None


def fetch_potion_by_slug(slug: str) -> Dict[str, Any]:
    try:
        url = f"{BASE_URL}/potions/{slug}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get("data")
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке зелья {slug}: {e}")
        return None


def fetch_all_books() -> list:
    try:
        url = f"{BASE_URL}/books"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get("data", [])
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке книг: {e}")
        return []


def format_character_text(character: Dict[str, Any]) -> str:
    """
    Форматирует данные о персонаже в текстовый формат
    """
    attrs = character.get("attributes", {})
    
    text_parts = []
    text_parts.append(f"Имя: {attrs.get('name', 'Неизвестно')}")
    
    if attrs.get("born"):
        text_parts.append(f"Дата рождения: {attrs['born']}")
    
    if attrs.get("died"):
        text_parts.append(f"Дата смерти: {attrs['died']}")
    
    if attrs.get("species"):
        text_parts.append(f"Вид: {attrs['species']}")
    
    if attrs.get("gender"):
        text_parts.append(f"Пол: {attrs['gender']}")
    
    if attrs.get("house"):
        text_parts.append(f"Факультет: {attrs['house']}")
    
    if attrs.get("wands"):
        wands = attrs["wands"]
        if isinstance(wands, list) and wands:
            text_parts.append(f"Палочки: {', '.join(wands)}")
    
    if attrs.get("patronus"):
        text_parts.append(f"Патронус: {attrs['patronus']}")
    
    if attrs.get("alias_names"):
        aliases = attrs["alias_names"]
        if isinstance(aliases, list) and aliases:
            text_parts.append(f"Другие имена: {', '.join(aliases)}")
    
    if attrs.get("animagus"):
        text_parts.append(f"Анимаг: {attrs['animagus']}")
    
    if attrs.get("blood_status"):
        text_parts.append(f"Кровное происхождение: {attrs['blood_status']}")
    
    if attrs.get("marital_status"):
        text_parts.append(f"Семейное положение: {attrs['marital_status']}")
    
    if attrs.get("nationality"):
        text_parts.append(f"Национальность: {attrs['nationality']}")
    
    if attrs.get("eye_color"):
        text_parts.append(f"Цвет глаз: {attrs['eye_color']}")
    
    if attrs.get("hair_color"):
        text_parts.append(f"Цвет волос: {attrs['hair_color']}")
    
    if attrs.get("height"):
        text_parts.append(f"Рост: {attrs['height']}")
    
    if attrs.get("boggart"):
        text_parts.append(f"Боггарт: {attrs['boggart']}")
    
    if attrs.get("jobs"):
        jobs = attrs["jobs"]
        if isinstance(jobs, list) and jobs:
            text_parts.append(f"Профессии: {', '.join(jobs)}")
    
    if attrs.get("family_members"):
        family = attrs["family_members"]
        if isinstance(family, list) and family:
            text_parts.append(f"Семья: {', '.join(family[:10])}")  # Первые 10 членов семьи
    
    return "\n".join(text_parts)


def format_spell_text(spell: Dict[str, Any]) -> str:
    attrs = spell.get("attributes", {})
    
    text_parts = []
    text_parts.append(f"Название: {attrs.get('name', 'Неизвестно')}")
    
    if attrs.get("incantation"):
        text_parts.append(f"Инкарнация: {attrs['incantation']}")
    
    if attrs.get("category"):
        text_parts.append(f"Категория: {attrs['category']}")
    
    if attrs.get("effect"):
        text_parts.append(f"Эффект: {attrs['effect']}")
    
    if attrs.get("light"):
        text_parts.append(f"Цвет света: {attrs['light']}")
    
    if attrs.get("hand"):
        text_parts.append(f"Жест: {attrs['hand']}")
    
    if attrs.get("creator"):
        text_parts.append(f"Создатель: {attrs['creator']}")
    
    return "\n".join(text_parts)


def format_potion_text(potion: Dict[str, Any]) -> str:
    attrs = potion.get("attributes", {})
    
    text_parts = []
    text_parts.append(f"Название: {attrs.get('name', 'Неизвестно')}")
    
    if attrs.get("effect"):
        text_parts.append(f"Эффект: {attrs['effect']}")
    
    if attrs.get("side_effects"):
        text_parts.append(f"Побочные эффекты: {attrs['side_effects']}")
    
    if attrs.get("characteristics"):
        text_parts.append(f"Характеристики: {attrs['characteristics']}")
    
    if attrs.get("time"):
        text_parts.append(f"Время приготовления: {attrs['time']}")
    
    if attrs.get("difficulty"):
        text_parts.append(f"Сложность: {attrs['difficulty']}")
    
    if attrs.get("ingredients"):
        ingredients = attrs["ingredients"]
        if isinstance(ingredients, list) and ingredients:
            text_parts.append(f"Ингредиенты: {', '.join(ingredients)}")
    
    if attrs.get("inventors"):
        inventors = attrs["inventors"]
        if isinstance(inventors, list) and inventors:
            text_parts.append(f"Изобретатели: {', '.join(inventors)}")
    
    return "\n".join(text_parts)


def format_book_text(book: Dict[str, Any]) -> str:
    attrs = book.get("attributes", {})
    
    text_parts = []
    text_parts.append(f"Название: {attrs.get('title', 'Неизвестно')}")
    
    if attrs.get("author"):
        text_parts.append(f"Автор: {attrs['author']}")
    
    if attrs.get("release_date"):
        text_parts.append(f"Дата выхода: {attrs['release_date']}")
    
    if attrs.get("pages"):
        text_parts.append(f"Количество страниц: {attrs['pages']}")
    
    if attrs.get("summary"):
        text_parts.append(f"Описание: {attrs['summary']}")
    
    if attrs.get("dedication"):
        text_parts.append(f"Посвящение: {attrs['dedication']}")
    
    return "\n".join(text_parts)


def save_character(character: Dict[str, Any], output_dir: Path):
    attrs = character.get("attributes", {})
    name = attrs.get("name", "unknown")
    slug = attrs.get("slug", "unknown")
    safe_name = slug.lower().replace(" ", "_").replace("/", "_").replace("\\", "_")
    filename = f"{safe_name}.txt"
    filepath = output_dir / filename
    
    text = format_character_text(character)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    
    print(f"Сохранен персонаж: {name}")


def save_spell(spell: Dict[str, Any], output_dir: Path):
    attrs = spell.get("attributes", {})
    name = attrs.get("name", "unknown")
    slug = attrs.get("slug", "unknown")
    safe_name = slug.lower().replace(" ", "_").replace("/", "_").replace("\\", "_")
    filename = f"{safe_name}.txt"
    filepath = output_dir / filename
    
    text = format_spell_text(spell)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    
    print(f"Сохранено заклинание: {name}")


def save_potion(potion: Dict[str, Any], output_dir: Path):
    attrs = potion.get("attributes", {})
    name = attrs.get("name", "unknown")
    slug = attrs.get("slug", "unknown")
    safe_name = slug.lower().replace(" ", "_").replace("/", "_").replace("\\", "_")
    filename = f"{safe_name}.txt"
    filepath = output_dir / filename
    
    text = format_potion_text(potion)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    
    print(f"Сохранено зелье: {name}")


def save_book(book: Dict[str, Any], output_dir: Path):
    attrs = book.get("attributes", {})
    title = attrs.get("title", "unknown")
    slug = attrs.get("slug", "unknown")
    safe_name = slug.lower().replace(" ", "_").replace("/", "_").replace("\\", "_")
    filename = f"{safe_name}.txt"
    filepath = output_dir / filename
    
    text = format_book_text(book)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    
    print(f"Сохранена книга: {title}")


def main():
    base_dir = Path("knowledge_base_raw")
    base_dir.mkdir(exist_ok=True)

    characters_dir = base_dir / "characters"
    spells_dir = base_dir / "spells"
    potions_dir = base_dir / "potions"
    books_dir = base_dir / "books"
    
    for dir_path in [characters_dir, spells_dir, potions_dir, books_dir]:
        dir_path.mkdir(exist_ok=True)
    
    stats = {
        "characters": 0,
        "spells": 0,
        "potions": 0,
        "books": 0
    }
    
    print("=" * 60)
    print("Загрузка данных из PotterDB API")
    print("=" * 60)
    
    print("\n1. Загрузка популярных персонажей...")
    for slug in POPULAR_CHARACTERS:
        character = fetch_character_by_slug(slug)
        if character:
            save_character(character, characters_dir)
            stats["characters"] += 1
        else:
            print(f"Персонаж не найден: {slug}")
        time.sleep(0.3)  # Задержка между запросами
    
    print("\n2. Загрузка популярных заклинаний...")
    for slug in POPULAR_SPELLS:
        spell = fetch_spell_by_slug(slug)
        if spell:
            save_spell(spell, spells_dir)
            stats["spells"] += 1
        else:
            print(f"Заклинание не найдено: {slug}")
        time.sleep(0.3)  # Задержка между запросами
    
    print("\n3. Загрузка популярных зелий...")
    for slug in POPULAR_POTIONS:
        potion = fetch_potion_by_slug(slug)
        if potion:
            save_potion(potion, potions_dir)
            stats["potions"] += 1
        else:
            print(f"Зелье не найдено: {slug}")
        time.sleep(0.3)  # Задержка между запросами
    
    print("\n4. Загрузка книг...")
    books = fetch_all_books()
    for book in books:
        save_book(book, books_dir)
        stats["books"] += 1
    
    stats_file = base_dir / "download_stats.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("Загрузка завершена!")
    print("=" * 60)
    print(f"Персонажей: {stats['characters']}")
    print(f"Заклинаний: {stats['spells']}")
    print(f"Зелий: {stats['potions']}")
    print(f"Книг: {stats['books']}")
    print(f"Всего: {sum(stats.values())} файлов")
    print(f"\nДанные сохранены в: {base_dir.absolute()}")


if __name__ == "__main__":
    main()
