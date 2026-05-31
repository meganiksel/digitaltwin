# Удалённые сущности из базы знаний (Задание 7)

Чтобы оценить, как бот ведёт себя на «слепых пятнах» (вопросах, на которые
в базе знаний нет ответа), из `knowledge_base/` намеренно удалены следующие
документы. Они присутствуют в исходной `knowledge_base_raw/`, поэтому при
необходимости их можно вернуть.

| Сущность | Файл(ы) | Категория | Зачем удалили |
|----------|---------|-----------|---------------|
| Альбус Дамблдор | `knowledge_base/characters/albus-dumbledore.txt` | character | Самый известный персонаж — бот ОБЯЗАН ответить «Я не знаю». |
| Зелье Pepperup (Бодроперцовое) | `knowledge_base/potions/pepperup_potion.txt`, `pepperup-potion.txt` | potion | Очевидный кейс зелья «при простуде». |
| Беллатриса Лестрейндж | `knowledge_base/characters/bellatrix-lestrange.txt` | character | Контрольный кейс на популярный второстепенный персонаж. |

## Как использовать

1. Запустить `python scripts/evaluate.py`. В `scripts/golden_questions.jsonl`
   вопросы про удалённые сущности помечены `category: "missing"` — бот должен
   отвечать «Я не знаю».
2. После эксперимента файлы можно восстановить из `knowledge_base_raw/`:
   ```bash
   cp knowledge_base_raw/characters/albus-dumbledore.txt knowledge_base/characters/
   cp knowledge_base_raw/potions/pepperup_potion.txt knowledge_base/potions/
   cp knowledge_base_raw/potions/pepperup-potion.txt knowledge_base/potions/
   cp knowledge_base_raw/characters/bellatrix-lestrange.txt knowledge_base/characters/
   python scripts/update_index.py  # инкрементальное обновление
   ```
