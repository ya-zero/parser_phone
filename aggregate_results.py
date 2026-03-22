#!/usr/bin/env python3
"""
Агрегация результатов парсинга из нескольких JSON файлов
Использование: ./aggregate_results.py crawl_*.json
"""

import sys
import json
from collections import defaultdict, Counter
from datetime import datetime


def aggregate_results(json_files):
    """
    Агрегирует результаты из нескольких JSON файлов
    
    Args:
        json_files: Список путей к JSON файлам
    """
    # Общая статистика
    all_phones = set()
    phones_by_domain = defaultdict(set)
    phones_by_city_code = defaultdict(set)
    total_pages = 0
    total_errors = 0
    domains_processed = set()
    
    # Загрузка всех файлов
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            domain = data.get('domain', 'unknown')
            domains_processed.add(domain)
            
            # Статистика
            total_pages += data['statistics']['pages_visited']
            total_errors += data['statistics']['errors']
            
            # Номера
            for phone in data['all_phones']:
                all_phones.add(phone)
                phones_by_domain[domain].add(phone)
                
                # Извлекаем код города
                import re
                match = re.match(r'\+\d+\((\d+)\)', phone)
                if match:
                    city_code = match.group(1)
                    phones_by_city_code[city_code].add(phone)
        
        except Exception as e:
            print(f"❌ Ошибка чтения {json_file}: {e}", file=sys.stderr)
            continue
    
    # Вывод сводного отчёта
    print("="*70)
    print("СВОДНЫЙ ОТЧЁТ ПО ПАРСИНГУ")
    print("="*70)
    print(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Обработано файлов: {len(json_files)}")
    print(f"Доменов: {len(domains_processed)}")
    print(f"Всего страниц: {total_pages}")
    print(f"Всего ошибок: {total_errors}")
    print(f"Уникальных номеров: {len(all_phones)}")
    print("="*70 + "\n")
    
    # Все уникальные номера
    print("ВСЕ УНИКАЛЬНЫЕ НОМЕРА")
    print("-"*70)
    for i, phone in enumerate(sorted(all_phones), 1):
        print(f"{i:3d}. {phone}")
    print()
    
    # По доменам
    if len(domains_processed) > 1:
        print("="*70)
        print("НОМЕРА ПО ДОМЕНАМ")
        print("="*70 + "\n")
        
        for domain in sorted(phones_by_domain.keys()):
            phones = phones_by_domain[domain]
            print(f"{domain} ({len(phones)} номеров)")
            for phone in sorted(phones):
                print(f"  • {phone}")
            print()
    
    # По кодам городов
    print("="*70)
    print("РАСПРЕДЕЛЕНИЕ ПО КОДАМ ГОРОДОВ")
    print("="*70 + "\n")
    
    city_stats = Counter()
    for city_code, phones in phones_by_city_code.items():
        city_stats[city_code] = len(phones)
    
    for city_code, count in city_stats.most_common():
        print(f"Код {city_code}: {count} номеров")
        for phone in sorted(phones_by_city_code[city_code])[:5]:
            print(f"  • {phone}")
        if len(phones_by_city_code[city_code]) > 5:
            print(f"  ... и ещё {len(phones_by_city_code[city_code]) - 5}")
        print()
    
    # Сохранение агрегированного результата
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"aggregate_{timestamp}.json"
    
    aggregate_data = {
        'timestamp': datetime.now().isoformat(),
        'source_files': json_files,
        'statistics': {
            'domains_processed': len(domains_processed),
            'total_pages': total_pages,
            'total_unique_phones': len(all_phones),
            'total_errors': total_errors
        },
        'all_phones': sorted(list(all_phones)),
        'phones_by_domain': {
            domain: sorted(list(phones)) 
            for domain, phones in phones_by_domain.items()
        },
        'phones_by_city_code': {
            code: sorted(list(phones))
            for code, phones in phones_by_city_code.items()
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(aggregate_data, f, ensure_ascii=False, indent=2)
    
    print("="*70)
    print(f"✓ Агрегированные результаты сохранены в {output_file}")
    print("="*70)


def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  {sys.argv[0]} <json_file1> [json_file2] ...")
        print(f"  {sys.argv[0]} crawl_*.json")
        print("\nПример:")
        print(f"  {sys.argv[0]} crawl_20260322_*.json")
        sys.exit(1)
    
    json_files = sys.argv[1:]
    
    # Проверка существования файлов
    import os
    valid_files = [f for f in json_files if os.path.exists(f)]
    
    if not valid_files:
        print("❌ Не найдено валидных JSON файлов", file=sys.stderr)
        sys.exit(1)
    
    aggregate_results(valid_files)


if __name__ == '__main__':
    main()
