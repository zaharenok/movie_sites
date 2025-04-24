import asyncio
import json
import pandas as pd
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse

class MovieSitesScraper:
    def __init__(self):
        self.sites = set()
        self.max_results = 100
        self.search_queries = [
            "watch movies online free india",
            "watch movies online free latin america",
            "stream movies online free india",
            "stream movies online free latin america",
            "online movie streaming sites india",
            "online movie streaming sites latin america"
        ]

    async def scrape_google(self, page, query):
        try:
            await page.goto('https://www.google.com')
            await page.wait_for_selector('textarea[name="q"]')
            await page.fill('textarea[name="q"]', query)
            await page.keyboard.press('Enter')
            await page.wait_for_load_state('networkidle')
            
            # Прокручиваем страницу несколько раз для получения большего количества результатов
            for _ in range(3):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(2)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Ищем все ссылки в результатах поиска
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.startswith('http'):
                    # Извлекаем домен
                    domain = urlparse(href).netloc
                    if domain and domain not in self.sites:
                        self.sites.add(domain)
                        print(f"Найден новый сайт: {domain}")
                        
                        if len(self.sites) >= self.max_results:
                            return True
        except Exception as e:
            print(f"Ошибка при поиске по запросу '{query}': {str(e)}")
        return False

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Используем Chromium
            page = await browser.new_page()
            
            for query in self.search_queries:
                if len(self.sites) >= self.max_results:
                    break
                    
                print(f"Поиск по запросу: {query}")
                if await self.scrape_google(page, query):
                    break
                
                # Пауза между запросами
                await asyncio.sleep(5)
            
            await browser.close()
            
            # Сохраняем результаты в JSON
            results = list(self.sites)
            with open('movie_sites.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            
            # Создаем DataFrame и сохраняем в CSV
            df = pd.DataFrame(results, columns=['domain'])
            df.to_csv('movie_sites.csv', index=False)
            
            print(f"\nНайдено {len(results)} уникальных сайтов")
            print("Результаты сохранены в movie_sites.json и movie_sites.csv")

if __name__ == "__main__":
    scraper = MovieSitesScraper()
    asyncio.run(scraper.run()) 