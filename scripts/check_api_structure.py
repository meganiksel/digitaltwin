#!/usr/bin/env python3
"""
Скрипт для проверки структуры данных API PotterDB
"""

import requests
import json

BASE_URL = "https://api.potterdb.com/v1"

# Проверяем первые 5 заклинаний
print("=== Заклинания ===")
response = requests.get(f"{BASE_URL}/spells?page[number]=1&page[size]=5", timeout=30)
data = response.json()

for item in data.get("data", [])[:5]:
    attrs = item.get("attributes", {})
    print(f"Name: {attrs.get('name')}")
    print(f"Incantation: {attrs.get('incantation')}")
    print(f"Effect: {attrs.get('effect')}")
    print("---")

# Проверяем первые 5 персонажей
print("\n=== Персонажи ===")
response = requests.get(f"{BASE_URL}/characters?page[number]=1&page[size]=5", timeout=30)
data = response.json()

for item in data.get("data", [])[:5]:
    attrs = item.get("attributes", {})
    print(f"Name: {attrs.get('name')}")
    print(f"House: {attrs.get('house')}")
    print("---")

# Ищем Harry Potter
print("\n=== Поиск Harry Potter ===")
response = requests.get(f"{BASE_URL}/characters?page[number]=1&page[size]=100", timeout=30)
data = response.json()

for item in data.get("data", []):
    attrs = item.get("attributes", {})
    name = attrs.get("name", "")
    if "harry" in name.lower():
        print(f"Found: {name}")
        print(f"House: {attrs.get('house')}")
        print(f"Born: {attrs.get('born')}")
        print("---")
