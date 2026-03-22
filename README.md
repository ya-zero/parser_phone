# Быстрый старт

## Два варианта парсера

### 1. phone_parser.py - Одна страница
Для быстрого парсинга одной страницы:

```bash
./phone_parser.py https://example.com
```

### 2. phone_crawler.py - Весь сайт ⭐ РЕКОМЕНДУЕТСЯ
Для рекурсивного обхода всех страниц сайта:

```bash
./phone_crawler.py https://example.com
```

## Типичные сценарии использования

### Сценарий 1: Быстрый сбор контактов
```bash
# Обход сайта с параметрами по умолчанию
chmod +x phone_crawler.py
./phone_crawler.py https://company.com

# Результат:
# - Автоматический обход всех внутренних страниц
# - Вывод процесса в реальном времени
# - Сохранение в 3 форматах: TXT, CSV, JSON
```

### Сценарий 2: Парсинг нескольких сайтов
```bash
# Создайте скрипт
cat > parse_sites.sh << 'EOF'
#!/bin/bash
for site in company1.com company2.com company3.com; do
    echo "Парсинг $site..."
    python3 phone_crawler.py "https://$site" json 2 50 1.0
done

# Объединить результаты
python3 aggregate_results.py crawl_*.json > report.txt
EOF

chmod +x parse_sites.sh
./parse_sites.sh
```

### Сценарий 3: Глубокий обход большого сайта
```bash
# Большая глубина, больше страниц, увеличенная задержка
./phone_crawler.py https://bigcompany.com all 5 500 2.0
```

### Сценарий 4: Быстрый сбор (малая задержка)
```bash
# Для своего сайта или когда нагрузка не критична
./phone_crawler.py https://mysite.com json 2 30 0.3
```

## Параметры командной строки

```bash
phone_crawler.py <URL> [формат] [глубина] [макс_страниц] [задержка]
```

| Параметр | Значения | По умолчанию | Описание |
|----------|----------|--------------|----------|
| URL | любой URL | - | Начальная страница |
| формат | txt/csv/json/all | all | Форматы сохранения |
| глубина | 1-10 | 3 | Уровни вложенности |
| макс_страниц | 10-1000 | 100 | Лимит страниц |
| задержка | 0.1-5.0 | 1.0 | Секунды между запросами |

## Форматы вывода

После обхода создаются файлы:

```
crawl_20260322_143000.txt   - Читаемый отчёт
crawl_20260322_143000.csv   - Для Excel/таблиц
crawl_20260322_143000.json  - Для программной обработки
```

## Примеры реальных команд

```bash
# Базовый обход корпоративного сайта
./phone_crawler.py https://company.ru

# Только CSV, малая глубина
./phone_crawler.py https://company.ru csv 2 50 0.5

# Глубокий обход без лимита
./phone_crawler.py https://company.ru all 10 1000 1.5

# Парсинг с сохранением только в JSON
./phone_crawler.py https://company.ru json
```

## Что делать с результатами

### Просмотр в консоли
```bash
# Все номера
cat crawl_*.txt

# Только номера
grep '^+' crawl_*.txt

# Номера Москвы (495)
grep '(495)' crawl_*.txt
```

### Импорт в Excel
Откройте файл `.csv` в Excel или LibreOffice Calc

### Программная обработка
```python
import json

with open('crawl_20260322_143000.json') as f:
    data = json.load(f)

print(f"Найдено номеров: {len(data['all_phones'])}")

# Группировка по кодам
for url, phones in data['phones_by_url'].items():
    print(f"{url}: {len(phones)} номеров")
```

### Агрегация из нескольких обходов
```bash
# Объединить результаты
python3 aggregate_results.py crawl_*.json > summary.txt
```

## Автоматизация

### Cron для регулярного парсинга
```bash
# Добавить в crontab
crontab -e

# Каждый день в 9:00
0 9 * * * cd /path/to/parser && ./phone_crawler.py https://company.com json >> crawler.log 2>&1
```

### Скрипт мониторинга конкурентов
```bash
#!/bin/bash
# monitor_competitors.sh

SITES=(
    "https://competitor1.com"
    "https://competitor2.com"
    "https://competitor3.com"
)

DATE=$(date +%Y%m%d)
REPORT_DIR="reports_$DATE"
mkdir -p "$REPORT_DIR"

cd "$REPORT_DIR"

for site in "${SITES[@]}"; do
    domain=$(echo "$site" | sed 's|https://||' | sed 's|/.*||')
    echo "Парсинг $domain..."
    
    python3 ../phone_crawler.py "$site" json 3 100 1.0
done

# Создать сводный отчёт
python3 ../aggregate_results.py crawl_*.json > aggregate_report.txt

echo "Отчёт сохранён в $REPORT_DIR/"
```

## Устранение проблем

### "Permission denied"
```bash
chmod +x phone_crawler.py
```

### "No module named..."
Используются только встроенные модули Python 3.6+, проверьте версию:
```bash
python3 --version
```

### Не находит номера
- Проверьте формат на сайте (должен быть +X(XXX)XXX-XX-XX)
- Увеличьте глубину обхода
- Проверьте, что сайт доступен без JavaScript

### Долго работает
- Уменьшите `макс_страниц`
- Уменьшите `глубину`
- Уменьшите `задержку` (осторожно!)

### 403/429 ошибки
- Увеличьте `задержку` до 2-3 секунд
- Сайт может блокировать автоматические запросы

## Дополнительные возможности

См. полную документацию в `README_CRAWLER.md`

- Использование как библиотеки Python
- Фильтрация результатов
- Экспорт в другие форматы (VCF, Markdown)
- Параллельный обход
- Работа через прокси
- JavaScript-сайты (Selenium)
