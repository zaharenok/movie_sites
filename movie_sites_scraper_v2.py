import asyncio
import json
import pandas as pd
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse
import random
import shadowsocks
import socket
import socks
import os

class MovieSitesScraper:
    def __init__(self):
        self.sites = set()
        self.max_results = 1500
        self.initial_delay = 10
        self.timeout = 120000
        self.max_tabs = 5  # Максимальное количество одновременно открытых вкладок
        self.tab_timeout = 300  # Таймаут для неактивных вкладок (в секундах)
        self.visited_pages = set()  # Кэш посещенных страниц
        self.active_tabs = {}  # Словарь активных вкладок {page_id: timestamp}
        
        # Список доменов для исключения
        self.excluded_domains = [
            'google.com', 'youtube.com', 'facebook.com', 'twitter.com', 'instagram.com',
            'linkedin.com', 'pinterest.com', 'reddit.com', 'tumblr.com', 'wikipedia.org',
            'yahoo.com', 'bing.com', 'duckduckgo.com', 'ecosia.org', 'qwant.com',
            'startpage.com', 'mojeek.com', 'gigablast.com', 'ask.com', 'amazon.com',
            'amazon.in', 'netflix.com', 'primevideo.com', 'disneyplus.com', 'hulu.com',
            'hbomax.com', 'peacocktv.com', 'paramountplus.com', 'appletv.com', 'crunchyroll.com',
            'funimation.com', 'justwatch.com', 'imdb.com', 'rottentomatoes.com', 'metacritic.com',
            'letterboxd.com', 'trakt.tv', 'tmdb.org', 'tvdb.com', 'anidb.net',
            'myanimelist.net', 'anilist.co', 'kitsu.io', 'aniwatch.to', '9anime.to',
            'gogoanime.io', 'animepahe.com', 'animekisa.tv', 'animeflv.net', 'animeid.tv',
            'animeheaven.ru', 'animefreak.tv', 'animeultima.to', 'kissasian.sh', 'dramacool.sx',
            'fmovies.to', 'soap2day.to', '123movies.to', 'putlocker.sx', 'goku.sx',
            'cinecalidad.onl', 'superflix.xyz', '0gomovies.ad', 'peliculaspanda.net', 'doramas.vip',
            'ennovelas.net', 'cinevibehd.com.br', 'topflixfm1.me', 'novelasflix1.me', 'dramanice.ws',
            'dramaspice.com', 'dramacool.sx', 'fmovies.to', 'soap2day.to', '123movies.to',
            'putlocker.sx', 'goku.sx', 'cinecalidad.onl', 'superflix.xyz', '0gomovies.ad',
            'peliculaspanda.net', 'doramas.vip', 'ennovelas.net', 'cinevibehd.com.br', 'topflixfm1.me',
            'novelasflix1.me', 'dramanice.ws', 'dramaspice.com', 'kissasian.org', 'dramacool.sx',
            'fmovies.to', 'soap2day.to', '123movies.to', 'putlocker.sx', 'goku.sx',
            'animepahe.com', 'animekisa.tv', 'animeflv.net', 'animeid.tv', 'animeheaven.ru',
            'animefreak.tv', 'animeultima.to', 'animekisa.tv', 'animeflv.net', 'animeid.tv',
            'animeheaven.ru', 'animefreak.tv'
        ]
        
        # Загружаем существующие сайты из JSON, если файл существует
        if os.path.exists('movie_sites.json'):
            with open('movie_sites.json', 'r', encoding='utf-8') as f:
                self.sites = set(json.load(f))
                print(f"Загружено {len(self.sites)} существующих сайтов из базы")
        
        # Статистика
        self.stats = {
            'new_sites': 0,
            'duplicates': 0,
            'porn_sites': 0,
            'invalid_sites': 0,
            'total_processed': 0
        }
        
        # Настройки Outline VPN
        self.outline_vpn = {
            'india': {
                'server': '64.227.132.137',
                'port': 80,
                'method': 'chacha20-ietf-poly1305',
                'password': 'NYk8DkZqmDLUQzaSbb2K3N'
            }
        }
        
        # Настройки геолокации для разных регионов
        self.geolocations = {
            'india': {
                'latitude': 20.5937,
                'longitude': 78.9629,
                'accuracy': 90
            }
        }
        
        # Расширенный список поисковых запросов
        self.search_queries = [
            # Общие запросы для фильмов на английском
            "watch movies online free",
            "stream movies online free",
            "online movie streaming sites",
            "free movie streaming sites",
            "movie streaming websites",
            "watch series online free",
            "stream series online free",
            "online series streaming sites",
            "free series streaming sites",
            "series streaming websites",
            
            # Запросы для индийского контента на английском
            "watch hindi movies online free",
            "watch bollywood movies online free",
            "watch indian movies online free",
            "hindi movies streaming sites free",
            "bollywood movies streaming sites free",
            "indian movies streaming sites free",
            "watch hindi tv serials online free",
            "watch indian drama series free",
            "hindi tv serials streaming sites free",
            "indian drama series streaming sites free",
            
            # Запросы для индийского контента на хинди
            "हिंदी फिल्में ऑनलाइन देखें मुफ्त",
            "बॉलीवुड फिल्में ऑनलाइन देखें मुफ्त",
            "भारतीय फिल्में ऑनलाइन देखें मुफ्त",
            "हिंदी फिल्में स्ट्रीमिंग साइट्स मुफ्त",
            "बॉलीवुड फिल्में स्ट्रीमिंग साइट्स मुफ्त",
            "भारतीय फिल्में स्ट्रीमिंग साइट्स मुफ्त",
            "हिंदी टीवी सीरियल ऑनलाइन देखें मुफ्त",
            "भारतीय ड्रामा सीरीज ऑनलाइन देखें मुफ्त",
            "हिंदी टीवी सीरियल स्ट्रीमिंग साइट्स मुफ्त",
            "भारतीय ड्रामा सीरीज स्ट्रीमिंग साइट्स मुफ्त",
            
            # Запросы для латиноамериканского контента на испанском
            "ver películas online gratis latino",
            "ver series online gratis latino",
            "ver novelas online gratis latino",
            "ver doramas online latino gratis",
            "ver telenovelas online gratis",
            "películas online latino descargar",
            "series online latino descargar",
            "novelas online latino descargar",
            "doramas online latino descargar",
            "telenovelas online latino descargar",
            
            # Запросы для бразильского контента на португальском
            "assistir filmes online gratis brasil",
            "assistir series online gratis brasil",
            "assistir novelas online gratis brasil",
            "assistir doramas online gratis brasil",
            "assistir telenovelas online gratis brasil",
            "filmes online brasil descargar",
            "series online brasil descargar",
            "novelas online brasil descargar",
            "doramas online brasil descargar",
            "telenovelas online brasil descargar",
            
            # Запросы для азиатского контента
            "watch korean drama online free",
            "watch chinese drama online free",
            "watch japanese drama online free",
            "watch thai drama online free",
            "watch taiwanese drama online free",
            "korean drama streaming sites free",
            "chinese drama streaming sites free",
            "japanese drama streaming sites free",
            "thai drama streaming sites free",
            "taiwanese drama streaming sites free",
            
            # Запросы для альтернативных сайтов
            "alternatives to netflix",
            "alternatives to prime video",
            "alternatives to disney plus",
            "alternatives to hulu",
            "alternatives to hbo max",
            "alternatives to peacock tv",
            "alternatives to paramount plus",
            "alternatives to apple tv plus",
            "alternatives to crunchyroll",
            "alternatives to funimation"
        ]
        
        # Список целевых доменов для поиска
        self.target_domains = [
            "cinecalidad.onl", "superflix.xyz", "0gomovies.ad",
            "peliculaspanda.net", "doramas.vip", "ennovelas.net",
            "cinevibehd.com.br", "topflixfm1.me", "novelasflix1.me",
            "dramanice.ws", "dramaspice.com", "kissasian.org",
            "dramacool.sx", "fmovies.to", "soap2day.to",
            "123movies.to", "putlocker.sx", "goku.sx",
            "animepahe.com", "animekisa.tv", "animeflv.net",
            "animeid.tv", "animeheaven.ru", "animefreak.tv",
            "animeultima.to", "animekisa.tv", "animeflv.net",
            "animeid.tv", "animeheaven.ru", "animefreak.tv"
        ]
        
        # Добавляем поиск по конкретным доменам с локализованными запросами
        for domain in self.target_domains:
            # Английские запросы
            self.search_queries.append(f"alternatives to {domain}")
            self.search_queries.append(f"similar to {domain}")
            self.search_queries.append(f"like {domain}")
            self.search_queries.append(f"better than {domain}")
            self.search_queries.append(f"replacement for {domain}")
            
            # Хинди запросы
            self.search_queries.append(f"{domain} के विकल्प")
            self.search_queries.append(f"{domain} जैसी साइटें")
            self.search_queries.append(f"{domain} के समान साइटें")
            
            # Испанские запросы
            self.search_queries.append(f"alternativas a {domain}")
            self.search_queries.append(f"sitios similares a {domain}")
            self.search_queries.append(f"mejor que {domain}")
            
            # Португальские запросы
            self.search_queries.append(f"alternativas para {domain}")
            self.search_queries.append(f"sites similares a {domain}")
            self.search_queries.append(f"melhor que {domain}")
            
            # Добавляем поиск по конкретным доменам
            self.search_queries.append(f"site:{domain}")
            self.search_queries.append(f"related:{domain}")
            self.search_queries.append(f"similar to {domain}")
            self.search_queries.append(f"alternatives to {domain}")
            self.search_queries.append(f"like {domain}")

        # Список поисковых систем (убрали Qwant)
        self.search_engines = [
            'https://www.google.com',
            'https://www.bing.com',
            'https://search.yahoo.com',
            'https://www.duckduckgo.com',
            'https://www.ecosia.org',
            'https://www.startpage.com',
            'https://www.mojeek.com',
            'https://www.gigablast.com',
            'https://www.ask.com'
        ]

    def setup_outline_vpn(self, region):
        """Настраивает Outline VPN для указанного региона"""
        vpn_config = self.outline_vpn[region]
        try:
            # Настраиваем SOCKS5 прокси
            socks.set_default_proxy(
                socks.SOCKS5,
                vpn_config['server'],
                vpn_config['port'],
                username='',
                password=vpn_config['password']
            )
            socket.socket = socks.socksocket
            
            # Проверяем подключение
            test_socket = socket.socket()
            test_socket.settimeout(5)
            test_socket.connect(('www.google.com', 80))
            test_socket.close()
            
            print(f"Outline VPN успешно настроен для региона {region}")
            return True
        except Exception as e:
            print(f"Ошибка при настройке Outline VPN: {e}")
            return False

    def is_valid_streaming_domain(self, domain):
        """Проверяет, является ли домен потенциальным стриминговым сайтом"""
        # Если домен в списке исключений
        if domain in self.excluded_domains:
            return False
            
        # Проверяем, не является ли домен поддоменом исключенных доменов
        for excluded in self.excluded_domains:
            if domain.endswith(f".{excluded}"):
                return False
        
        # Проверяем характерные признаки стриминговых сайтов
        streaming_keywords = [
            'movie', 'film', 'cinema', 'drama', 'serie', 'tv', 'show',
            'pelicula', 'novela', 'dorama', 'anime', 'stream', 'watch',
            'ver', 'assistir', 'flix', 'play', 'hd', 'online', 'video',
            'media', 'tube', 'hub', 'cast', 'view', 'watch', 'see',
            'look', 'view', 'streaming', 'player', 'channel', 'live',
            'broadcast', 'telecast', 'webcast', 'webinar', 'vod',
            'iptv', 'ott', 'catchup', 'replay', 'ondemand'
        ]
        
        # Проверяем наличие ключевых слов в домене
        domain_parts = domain.lower().replace('.', ' ').split()
        if any(keyword in domain_parts for keyword in streaming_keywords):
            return True
            
        # Проверяем характерные TLD для стриминговых сайтов
        streaming_tlds = [
            '.to', '.sx', '.ws', '.is', '.fun', '.tv', '.me', '.cc', '.vip',
            '.io', '.net', '.org', '.info', '.biz', '.site', '.online',
            '.xyz', '.club', '.pro', '.app', '.dev', '.tech', '.media',
            '.video', '.stream', '.watch', '.live', '.play', '.show',
            '.film', '.movie', '.cinema', '.theater', '.theatre', '.tv',
            '.video', '.media', '.stream', '.watch', '.live', '.play',
            '.show', '.film', '.movie', '.cinema', '.theater', '.theatre'
        ]
        if any(domain.endswith(tld) for tld in streaming_tlds):
            return True
            
        return False

    def is_porn_site(self, domain):
        """Проверяет, является ли сайт порно-сайтом"""
        porn_keywords = [
            'porn', 'xxx', 'sex', 'adult', 'nude', 'fuck', 'pussy', 'dick',
            'cock', 'cum', 'suck', 'ass', 'tits', 'boobs', 'naked', 'hentai'
        ]
        
        domain_parts = domain.lower().replace('.', ' ').split()
        return any(keyword in domain_parts for keyword in porn_keywords)

    async def save_results(self):
        """Сохраняет текущие результаты в файлы"""
        results = list(self.sites)
        with open('movie_sites.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        df = pd.DataFrame({
            'domain': results,
            'date_found': pd.Timestamp.now().strftime('%Y-%m-%d'),
            'category': ['streaming' for _ in results]
        })
        df.to_csv('movie_sites.csv', index=False)
        print(f"Результаты сохранены. Всего сайтов: {len(results)}")

    async def cleanup_inactive_tabs(self, context):
        """Очищает неактивные вкладки"""
        current_time = time.time()
        for page_id, timestamp in list(self.active_tabs.items()):
            if current_time - timestamp > self.tab_timeout:
                try:
                    page = context.pages[page_id]
                    await page.close()
                    del self.active_tabs[page_id]
                    print(f"Закрыта неактивная вкладка {page_id}")
                except Exception as e:
                    print(f"Ошибка при закрытии вкладки {page_id}: {e}")

    async def get_new_page(self, context):
        """Получает новую вкладку с учетом ограничений"""
        # Очищаем неактивные вкладки
        await self.cleanup_inactive_tabs(context)
        
        # Если достигнут лимит вкладок, закрываем самую старую
        if len(self.active_tabs) >= self.max_tabs:
            oldest_page_id = min(self.active_tabs.items(), key=lambda x: x[1])[0]
            try:
                page = context.pages[oldest_page_id]
                await page.close()
                del self.active_tabs[oldest_page_id]
                print(f"Закрыта старая вкладка {oldest_page_id}")
            except Exception as e:
                print(f"Ошибка при закрытии старой вкладки: {e}")
        
        # Создаем новую вкладку
        page = await context.new_page()
        self.active_tabs[page.page_id] = time.time()
        return page

    async def scrape_google(self, page, query, region):
        try:
            # Проверяем, не посещали ли мы уже эту страницу
            page_key = f"{query}_{region}"
            if page_key in self.visited_pages:
                print(f"Пропускаем уже проверенную страницу: {query}")
                return False
            self.visited_pages.add(page_key)
            
            # Обновляем время последней активности вкладки
            self.active_tabs[page.page_id] = time.time()
            
            # Устанавливаем геолокацию для текущего региона
            await page.context.set_geolocation(self.geolocations[region])
            
            # Используем разные поисковые системы
            search_engine = random.choice(self.search_engines)
            await page.goto(search_engine, timeout=self.timeout)
            
            # Ждем появления поисковой строки
            if 'google' in search_engine:
                await page.wait_for_selector('textarea[name="q"]', timeout=self.timeout)
                await page.fill('textarea[name="q"]', query)
            elif 'bing' in search_engine:
                await page.wait_for_selector('#sb_form_q', timeout=self.timeout)
                await page.fill('#sb_form_q', query)
            elif 'yahoo' in search_engine:
                await page.wait_for_selector('#yschsp', timeout=self.timeout)
                await page.fill('#yschsp', query)
            else:
                # Для других поисковиков используем общий селектор
                await page.wait_for_selector('input[type="text"], input[type="search"]', timeout=self.timeout)
                await page.fill('input[type="text"], input[type="search"]', query)
            
            await page.keyboard.press('Enter')
            await page.wait_for_load_state('networkidle', timeout=self.timeout)
            
            page_count = 0
            max_pages = 30
            
            while page_count < max_pages:
                # Прокручиваем страницу несколько раз
                for _ in range(5):
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(1)
                
                # Очищаем память после прокрутки
                await page.evaluate('window.gc()')
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Собираем все ссылки на странице
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and href.startswith('http'):
                        try:
                            # Извлекаем домен
                            domain = urlparse(href).netloc.lower()
                            
                            self.stats['total_processed'] += 1
                            
                            # Проверяем, не порно ли это
                            if self.is_porn_site(domain):
                                self.stats['porn_sites'] += 1
                                continue
                            
                            # Проверяем домен на валидность
                            if domain and domain not in self.sites and self.is_valid_streaming_domain(domain):
                                self.sites.add(domain)
                                self.stats['new_sites'] += 1
                                print(f"Найден новый стриминговый сайт: {domain} (Всего: {len(self.sites)})")
                                
                                # Сохраняем результаты после каждого найденного сайта
                                await self.save_results()
                                
                                if len(self.sites) >= self.max_results:
                                    return True
                            elif domain in self.sites:
                                self.stats['duplicates'] += 1
                        except Exception as e:
                            self.stats['invalid_sites'] += 1
                            print(f"Ошибка при обработке ссылки {href}: {str(e)}")
                
                page_count += 1
                
                if page_count >= max_pages:
                    break
                
                # Пробуем найти кнопку следующей страницы
                next_button = None
                try:
                    if 'google' in search_engine:
                        next_button = await page.query_selector('text=Следующая')
                    elif 'bing' in search_engine:
                        next_button = await page.query_selector('text=Next')
                    elif 'yahoo' in search_engine:
                        next_button = await page.query_selector('text=Next')
                    else:
                        next_button = await page.query_selector('text=Next, text=Следующая, text=Next page')
                    
                    if next_button:
                        await next_button.click()
                        await page.wait_for_load_state('networkidle', timeout=self.timeout)
                        await asyncio.sleep(1)
                    else:
                        break
                except Exception as e:
                    print(f"Ошибка при переходе на следующую страницу: {str(e)}")
                    break
                    
        except Exception as e:
            print(f"Ошибка при поиске по запросу '{query}': {str(e)}")
        return False

    async def run(self):
        print(f"Ожидание {self.initial_delay} секунд перед началом...")
        await asyncio.sleep(self.initial_delay)
        
        # Настраиваем Outline VPN для Индии
        if not self.setup_outline_vpn('india'):
            print("Не удалось настроить VPN. Продолжаем без VPN.")
        
        async with async_playwright() as p:
            # Создаем браузер в headless режиме
            browser = await p.chromium.launch(headless=True)
            
            # Создаем контекст с настройками геолокации
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                locale='en-IN',
                timezone_id='Asia/Kolkata'
            )
            
            try:
                # Перемешиваем запросы
                random.shuffle(self.search_queries)
                
                # Используем только Индию как регион
                region = 'india'
                
                for query in self.search_queries:
                    if len(self.sites) >= self.max_results:
                        break
                    
                    print(f"\nПоиск по запросу: {query}")
                    
                    # Получаем новую вкладку
                    page = await self.get_new_page(context)
                    
                    if await self.scrape_google(page, query, region):
                        break
                    
                    # Минимальная пауза между запросами
                    await asyncio.sleep(1)
                    
                    # Очищаем неактивные вкладки после каждого запроса
                    await self.cleanup_inactive_tabs(context)
            except KeyboardInterrupt:
                print("\nПолучен сигнал прерывания. Сохраняем текущие результаты...")
            finally:
                # Закрываем все вкладки
                for page in context.pages:
                    try:
                        await page.close()
                    except:
                        pass
                await browser.close()
                await self.save_results()
                
                # Выводим итоговую статистику
                print("\n=== ИТОГОВАЯ СТАТИСТИКА ===")
                print(f"Всего сайтов в базе: {len(self.sites)}")
                print(f"Новых сайтов найдено: {self.stats['new_sites']}")
                print(f"Дубликатов найдено: {self.stats['duplicates']}")
                print(f"Порно-сайтов отфильтровано: {self.stats['porn_sites']}")
                print(f"Невалидных сайтов: {self.stats['invalid_sites']}")
                print(f"Всего обработано сайтов: {self.stats['total_processed']}")
                print("Результаты сохранены в movie_sites.json и movie_sites.csv")

if __name__ == "__main__":
    scraper = MovieSitesScraper()
    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        print("\nПолучен сигнал прерывания. Сохраняем текущие результаты...")
        # Сохраняем результаты
        results = list(scraper.sites)
        with open('movie_sites.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        # Создаем DataFrame с дополнительной информацией
        df = pd.DataFrame({
            'domain': results,
            'date_found': pd.Timestamp.now().strftime('%Y-%m-%d'),
            'category': ['streaming' for _ in results]
        })
        df.to_csv('movie_sites.csv', index=False)
        
        # Выводим итоговую статистику
        print("\n=== ИТОГОВАЯ СТАТИСТИКА ===")
        print(f"Всего сайтов в базе: {len(results)}")
        print(f"Новых сайтов найдено: {scraper.stats['new_sites']}")
        print(f"Дубликатов найдено: {scraper.stats['duplicates']}")
        print(f"Порно-сайтов отфильтровано: {scraper.stats['porn_sites']}")
        print(f"Невалидных сайтов: {scraper.stats['invalid_sites']}")
        print(f"Всего обработано сайтов: {scraper.stats['total_processed']}")
        print("Результаты сохранены в movie_sites.json и movie_sites.csv") 