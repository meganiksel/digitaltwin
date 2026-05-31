# Задание 2: Подготовка базы знаний

## Обзор

Задание 2 включает создание уникальной базы знаний на основе вселенной Гарри Поттера с заменой ключевых терминов на вымышленные.

## Структура

```
knowledge_base/
├── characters/          # Персонажи
├── locations/          # Места
├── spells/            # Заклинания
├── artifacts/         # Артефакты
└── terms_map.json     # Словарь замен

scripts/
├── download_wiki.py    # Скрипт для скачивания страниц
└── replace_terms.py   # Скрипт для замены терминов
```

## Шаг 1: Скачивание страниц с harrypotter.fandom.com

### Запуск скрипта

```bash
python scripts/download_wiki.py
```

### Что делает скрипт

1. Скачивает 30+ популярных страниц с harrypotter.fandom.com
2. Извлекает чистый текст из HTML
3. Сохраняет файлы в директорию `knowledge_base_raw/`

### Категории страниц

- **Персонажи (10)**: Harry Potter, Hermione Granger, Ron Weasley, Albus Dumbledore, Severus Snape, Lord Voldemort, Draco Malfoy, Sirius Black, Rubeus Hagrid, Minerva McGonagall
- **Места (8)**: Hogwarts, Diagon Alley, Ministry of Magic, Gringotts, Hogsmeade, Privet Drive, Azkaban, Platform 9¾
- **Заклинания (6)**: Expelliarmus, Avada Kedavra, Expecto Patronum, Lumos, Wingardium Leviosa, Alohomora
- **Артефакты (6)**: Elder Wand, Invisibility Cloak, Resurrection Stone, Sorting Hat, Marauder's Map, Time-Turner

### Результат

Файлы сохраняются в `knowledge_base_raw/` с такой же структурой категорий.

## Шаг 2: Замена терминов

### Запуск скрипта

```bash
python scripts/replace_terms.py
```

### Что делает скрипт

1. Загружает словарь замен из `knowledge_base/terms_map.json`
2. Обрабатывает все файлы из `knowledge_base_raw/`
3. Заменяет оригинальные термины на вымышленные
4. Сохраняет результаты в `knowledge_base/`

### Примеры замен

| Оригинал | Замена |
|----------|--------|
| Harry Potter | Xander Thornfield |
| Hermione Granger | Lyra Blackwood |
| Ron Weasley | Rowan Redford |
| Hogwarts | Arcanum Academy |
| Magic | Aether |
| Wand | Focus Staff |
| Spell | Incantation |
| Wizard | Adept |
| Muggle | Ordinary |

### Особенности замены

- Замена с учётом границ слов (чтобы избежать частичных замен)
- Сортировка по длине (сначала длинные фразы, затем короткие)
- Регистронезависимая замена (сохраняет оригинальный регистр)

## Шаг 3: Проверка результатов

После выполнения обоих скриптов проверьте:

1. **Количество файлов**: Должно быть 30+ файлов в `knowledge_base/`
2. **Качество замены**: Откройте несколько файлов и убедитесь, что термины заменены корректно
3. **Логичность текста**: Текст должен оставаться читаемым и логичным

## Структура словаря замен

`terms_map.json` организован по категориям:

```json
{
  "Персонажи": {
    "Harry Potter": "Xander Thornfield",
    ...
  },
  "Места": {
    "Hogwarts": "Arcanum Academy",
    ...
  },
  "Заклинания": {
    "Expelliarmus": "Dispel Force",
    ...
  },
  ...
}
```

## Добавление новых замен

Чтобы добавить новые замены:

1. Откройте `knowledge_base/terms_map.json`
2. Добавьте новую пару в соответствующую категорию
3. Перезапустите `scripts/replace_terms.py`

## Устранение проблем

### Проблема: Скрипт не может скачать страницу

**Решение:**
- Проверьте подключение к интернету
- Попробуйте запустить скрипт позже (возможно, сайт перегружен)
- Проверьте, что имя страницы указано правильно

### Проблема: Текст не извлекается

**Решение:**
- Проверьте HTML-код страницы (структура могла измениться)
- Попробуйте скачать другую страницу
- Отредактируйте функцию `extract_text_from_html` в `scripts/download_wiki.py`

### Проблема: Замена работает некорректно

**Решение:**
- Проверьте словарь замен на наличие конфликтов
- Убедитесь, что термины не пересекаются
- Отредактируйте функцию `replace_terms_in_text` в `scripts/replace_terms.py`

## Результат

После завершения Задания 2 у вас должно быть:

- ✅ 30+ документов в `knowledge_base/`
- ✅ Все ключевые термины заменены на вымышленные
- ✅ Тексты остаются логичными и читаемыми
- ✅ База знаний не распознаётся как вселенная Гарри Поттера

## Следующий шаг

Задание 3: Создание векторного индекса

```bash
python scripts/build_index.py
```
