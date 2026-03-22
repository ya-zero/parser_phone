#!/usr/bin/env python3
"""
Рекурсивный парсер телефонных номеров с сайтов
Обходит все внутренние страницы домена
Формат: код_страны(код_города)xxx-xx-xx
"""

import re
import sys
import json
import csv
from typing import Set, List, Dict
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
import time


class LinkExtractor(HTMLParser):
    """Извлекает ссылки из HTML"""
    
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.links = set()
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href':
                    # Преобразуем относительные ссылки в абсолютные
                    absolute_url = urljoin(self.base_url, value)
                    self.links.add(absolute_url)


class PhoneCrawler:
    """Рекурсивный парсер телефонных номеров"""
    
    def __init__(self, max_depth: int = 3, max_pages: int = 100, delay: float = 1.0):
        """
        Args:
            max_depth: Максимальная глубина рекурсии
            max_pages: Максимальное количество страниц для обхода
            delay: Задержка между запросами (в секундах)
        """
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        
        # Регулярное выражение для поиска номеров
        self.phone_pattern = re.compile(
            r'(?:\+?(\d{1,3}))?'        # Код страны
            r'\s*\((\d{3,4})\)'         # Код города
            r'\s*(\d{3})'               # Первая часть
            r'[-\s]?'
            r'(\d{2})'                  # Вторая часть
            r'[-\s]?'
            r'(\d{2})'                  # Третья часть
        )
        
        # Статистика обхода
        self.visited_urls = set()
        self.phones_by_url = {}
        self.all_phones = set()
        self.errors = {}
    
    def is_same_domain(self, url1: str, url2: str) -> bool:
        """Проверяет, принадлежат ли URL одному домену"""
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2
    
    def normalize_url(self, url: str) -> str:
        """Нормализует URL (удаляет якоря, параметры запроса опционально)"""
        parsed = urlparse(url)
        # Удаляем якорь (#)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # Добавляем query параметры (можно отключить для дедупликации)
        if parsed.query:
            normalized += f"?{parsed.query}"
        
        # Удаляем trailing slash для единообразия
        if normalized.endswith('/') and len(parsed.path) > 1:
            normalized = normalized[:-1]
        
        return normalized
    
    def should_visit(self, url: str, base_url: str) -> bool:
        """Определяет, нужно ли посещать URL"""
        normalized = self.normalize_url(url)
        
        # Уже посещали
        if normalized in self.visited_urls:
            return False
        
        # Не тот домен
        if not self.is_same_domain(url, base_url):
            return False
        
        # Достигли лимита страниц
        if len(self.visited_urls) >= self.max_pages:
            return False
        
        # Исключаем файлы (не HTML)
        excluded_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', 
                              '.css', '.js', '.zip', '.doc', '.docx', 
                              '.xls', '.xlsx', '.xml', '.json']
        
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        
        for ext in excluded_extensions:
            if path_lower.endswith(ext):
                return False
        
        return True
    
    def fetch_page(self, url: str, timeout: int = 10) -> str:
        """Загружает HTML страницы"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }
        
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as response:
            charset = response.headers.get_content_charset()
            if not charset:
                charset = 'utf-8'
            
            html = response.read().decode(charset, errors='ignore')
            return html
    
    def extract_links(self, html: str, base_url: str) -> Set[str]:
        """Извлекает все ссылки из HTML"""
        parser = LinkExtractor(base_url)
        try:
            parser.feed(html)
        except Exception:
            pass  # Игнорируем ошибки парсинга HTML
        
        return parser.links
    
    def parse_phones(self, text: str) -> Set[str]:
        """Извлекает телефонные номера из текста"""
        phones = set()
        
        for match in self.phone_pattern.finditer(text):
            country_code = match.group(1) or '7'
            city_code = match.group(2)
            part1 = match.group(3)
            part2 = match.group(4)
            part3 = match.group(5)
            
            phone = f"+{country_code}({city_code}){part1}-{part2}-{part3}"
            phones.add(phone)
        
        return phones
    
    def crawl_url(self, url: str, base_url: str, depth: int = 0, verbose: bool = True):
        """
        Рекурсивно обходит URL и все внутренние ссылки
        
        Args:
            url: URL для обхода
            base_url: Базовый URL сайта
            depth: Текущая глубина рекурсии
            verbose: Подробный вывод
        """
        # Проверяем условия остановки
        if depth > self.max_depth:
            return
        
        normalized_url = self.normalize_url(url)
        
        if not self.should_visit(url, base_url):
            return
        
        # Отмечаем как посещенный
        self.visited_urls.add(normalized_url)
        
        try:
            # Задержка между запросами (вежливость к серверу)
            if len(self.visited_urls) > 1:
                time.sleep(self.delay)
            
            if verbose:
                indent = "  " * depth
                print(f"{indent}🔍 [{len(self.visited_urls)}/{self.max_pages}] {normalized_url}")
            
            # Загружаем страницу
            html = self.fetch_page(url)
            
            # Парсим номера
            phones = self.parse_phones(html)
            
            if phones:
                self.phones_by_url[normalized_url] = phones
                self.all_phones.update(phones)
                
                if verbose:
                    indent = "  " * depth
                    print(f"{indent}  📞 Найдено номеров: {len(phones)}")
            
            # Извлекаем ссылки для рекурсивного обхода
            links = self.extract_links(html, url)
            
            # Рекурсивно обходим внутренние ссылки
            for link in links:
                if self.should_visit(link, base_url):
                    self.crawl_url(link, base_url, depth + 1, verbose)
        
        except HTTPError as e:
            self.errors[normalized_url] = f"HTTP {e.code}: {e.reason}"
            if verbose:
                indent = "  " * depth
                print(f"{indent}  ❌ HTTP {e.code}")
        
        except Exception as e:
            self.errors[normalized_url] = str(e)
            if verbose:
                indent = "  " * depth
                print(f"{indent}  ❌ Ошибка: {str(e)[:50]}")
    
    def crawl(self, start_url: str, verbose: bool = True):
        """
        Начинает обход сайта с указанного URL
        
        Args:
            start_url: Начальный URL
            verbose: Подробный вывод
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"Рекурсивный парсинг сайта")
            print(f"{'='*70}")
            print(f"Начальный URL: {start_url}")
            print(f"Макс. глубина: {self.max_depth}")
            print(f"Макс. страниц: {self.max_pages}")
            print(f"Задержка: {self.delay}s")
            print(f"{'='*70}\n")
        
        # Сброс статистики
        self.visited_urls.clear()
        self.phones_by_url.clear()
        self.all_phones.clear()
        self.errors.clear()
        
        # Запуск обхода
        start_time = time.time()
        self.crawl_url(start_url, start_url, depth=0, verbose=verbose)
        elapsed = time.time() - start_time
        
        # Вывод статистики
        if verbose:
            print(f"\n{'='*70}")
            print(f"Обход завершен за {elapsed:.1f}s")
            print(f"{'='*70}")
            print(f"Посещено страниц: {len(self.visited_urls)}")
            print(f"Страниц с номерами: {len(self.phones_by_url)}")
            print(f"Всего уникальных номеров: {len(self.all_phones)}")
            print(f"Ошибок: {len(self.errors)}")
            print(f"{'='*70}\n")
    
    def print_results(self):
        """Выводит подробные результаты обхода"""
        print("\n" + "="*70)
        print("НАЙДЕННЫЕ НОМЕРА")
        print("="*70 + "\n")
        
        if not self.all_phones:
            print("❌ Телефонные номера не найдены\n")
            return
        
        # Все уникальные номера
        print(f"Всего уникальных номеров: {len(self.all_phones)}\n")
        for i, phone in enumerate(sorted(self.all_phones), 1):
            print(f"{i:3d}. {phone}")
        
        # Номера по страницам
        print(f"\n{'='*70}")
        print("НОМЕРА ПО СТРАНИЦАМ")
        print("="*70 + "\n")
        
        for url in sorted(self.phones_by_url.keys()):
            phones = self.phones_by_url[url]
            print(f"📄 {url}")
            print(f"   Найдено: {len(phones)}")
            for phone in sorted(phones):
                print(f"   • {phone}")
            print()
        
        # Ошибки (если есть)
        if self.errors:
            print(f"{'='*70}")
            print("ОШИБКИ")
            print("="*70 + "\n")
            
            for url, error in sorted(self.errors.items()):
                print(f"❌ {url}")
                print(f"   {error}\n")
    
    def save_results(self, start_url: str, format: str = 'all'):
        """Сохраняет результаты обхода"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"crawl_{timestamp}"
        
        parsed_url = urlparse(start_url)
        domain = parsed_url.netloc.replace('www.', '')
        
        if format in ['txt', 'all']:
            # TXT файл
            txt_file = f"{base_filename}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(f"Рекурсивный парсинг сайта\n")
                f.write(f"{'='*70}\n")
                f.write(f"Начальный URL: {start_url}\n")
                f.write(f"Домен: {domain}\n")
                f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*70}\n\n")
                
                f.write(f"Статистика обхода:\n")
                f.write(f"  Посещено страниц: {len(self.visited_urls)}\n")
                f.write(f"  Страниц с номерами: {len(self.phones_by_url)}\n")
                f.write(f"  Всего номеров: {len(self.all_phones)}\n")
                f.write(f"  Ошибок: {len(self.errors)}\n\n")
                
                f.write(f"{'='*70}\n")
                f.write(f"ВСЕ НАЙДЕННЫЕ НОМЕРА ({len(self.all_phones)})\n")
                f.write(f"{'='*70}\n\n")
                
                for phone in sorted(self.all_phones):
                    f.write(f"{phone}\n")
                
                f.write(f"\n{'='*70}\n")
                f.write(f"НОМЕРА ПО СТРАНИЦАМ\n")
                f.write(f"{'='*70}\n\n")
                
                for url in sorted(self.phones_by_url.keys()):
                    phones = self.phones_by_url[url]
                    f.write(f"{url}\n")
                    f.write(f"Найдено: {len(phones)}\n")
                    for phone in sorted(phones):
                        f.write(f"  • {phone}\n")
                    f.write("\n")
            
            print(f"✓ Сохранено в {txt_file}")
        
        if format in ['csv', 'all']:
            # CSV файл
            csv_file = f"{base_filename}.csv"
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['URL', 'Телефон', 'Код страны', 'Код города', 'Номер'])
                
                for url in sorted(self.phones_by_url.keys()):
                    for phone in sorted(self.phones_by_url[url]):
                        match = re.match(r'\+(\d+)\((\d+)\)([\d-]+)', phone)
                        if match:
                            country = match.group(1)
                            city = match.group(2)
                            number = match.group(3)
                            writer.writerow([url, phone, country, city, number])
            
            print(f"✓ Сохранено в {csv_file}")
        
        if format in ['json', 'all']:
            # JSON файл
            json_file = f"{base_filename}.json"
            data = {
                'start_url': start_url,
                'domain': domain,
                'timestamp': datetime.now().isoformat(),
                'statistics': {
                    'pages_visited': len(self.visited_urls),
                    'pages_with_phones': len(self.phones_by_url),
                    'total_unique_phones': len(self.all_phones),
                    'errors': len(self.errors)
                },
                'all_phones': sorted(list(self.all_phones)),
                'phones_by_url': {
                    url: sorted(list(phones)) 
                    for url, phones in self.phones_by_url.items()
                },
                'visited_urls': sorted(list(self.visited_urls)),
                'errors': self.errors
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Сохранено в {json_file}")


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  {sys.argv[0]} <URL> [формат] [макс_глубина] [макс_страниц] [задержка]")
        print("\nПараметры:")
        print("  URL           - Начальный URL для обхода")
        print("  формат        - Формат сохранения: txt|csv|json|all (по умолчанию: all)")
        print("  макс_глубина  - Максимальная глубина рекурсии (по умолчанию: 3)")
        print("  макс_страниц  - Максимум страниц для обхода (по умолчанию: 100)")
        print("  задержка      - Задержка между запросами в сек (по умолчанию: 1.0)")
        print("\nПримеры:")
        print(f"  {sys.argv[0]} https://example.com")
        print(f"  {sys.argv[0]} https://example.com json 2 50 0.5")
        sys.exit(1)
    
    # Парсинг аргументов
    url = sys.argv[1]
    save_format = sys.argv[2] if len(sys.argv) > 2 else 'all'
    max_depth = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    max_pages = int(sys.argv[4]) if len(sys.argv) > 4 else 100
    delay = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
    
    if save_format not in ['txt', 'csv', 'json', 'all']:
        print(f"❌ Неверный формат: {save_format}", file=sys.stderr)
        sys.exit(1)
    
    # Создание crawler
    crawler = PhoneCrawler(
        max_depth=max_depth,
        max_pages=max_pages,
        delay=delay
    )
    
    # Обход сайта
    crawler.crawl(url, verbose=True)
    
    # Вывод результатов
    crawler.print_results()
    
    # Сохранение
    if crawler.all_phones:
        print(f"\n💾 Сохранение результатов...\n")
        crawler.save_results(url, format=save_format)
        print()


if __name__ == '__main__':
    main()
