import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from tqdm import tqdm

from scraper.config import USER_AGENTS, DELAY_RANGE, MAX_RETRIES, TIMEOUT, MAX_PAGES
from scraper.file_utils import save_to_csv


class OtomotoScraper:
    def __init__(self):
        self.session = requests.Session()

    def get_random_user_agent(self):
        return random.choice(USER_AGENTS)

    def get_page_count(self, soup):
        """Improved page count detection with multiple fallback methods"""
        try:
            # Method 1: Check pagination buttons
            page_buttons = soup.select('li[class*="ooa-"]:not([aria-label])')
            if page_buttons:
                page_numbers = []
                for btn in page_buttons:
                    text = btn.get_text(strip=True)
                    if text.isdigit():
                        page_numbers.append(int(text))

                if page_numbers:
                    return min(max(page_numbers), MAX_PAGES)

            # Method 2: Check next page button
            next_btn = soup.find('li', attrs={'aria-label': lambda x: x and 'next' in x.lower()})
            if next_btn and 'disabled' not in next_btn.get('class', []):
                return 2  # At least 2 pages if next button is active

        except Exception as e:
            print(f"Error detecting page count: {e}")

        return 1  # Default to 1 page

    def scrape_car_listing(self, listing, url):
        car = {}

        # --- Tytuł i link ---
        title_elem = listing.find('h2', {'data-sentry-element': 'Title'})
        if title_elem:
            full_title = title_elem.text.strip()
            title_parts = full_title.split()
            car['marka'] = title_parts[0] if len(title_parts) > 0 else 'Brak danych'
            car['model'] = title_parts[1] if len(title_parts) > 1 else 'Brak danych'
            car['opis'] = ' '.join(title_parts[2:]) if len(title_parts) > 2 else 'Brak danych'

            link_elem = title_elem.find('a')
            car['link'] = urljoin(url, link_elem['href']) if link_elem and 'href' in link_elem.attrs else 'Brak linku'
        else:
            car['marka'] = car['model'] = car['opis'] = 'Brak danych'
            car['link'] = 'Brak linku'

        # --- Cena ---
        price_elem = listing.find('h3', {'data-sentry-element': 'Price'})
        car['cena'] = price_elem.text.strip() if price_elem else 'Brak ceny'

        # --- Moc silnika w KM ---
        subtitle_elem = listing.find('p', {'data-sentry-element': 'SubTitle'})
        if subtitle_elem:
            subtitle_text = subtitle_elem.text.strip()
            moc_match = re.search(r'(\d+)\s*KM', subtitle_text, re.IGNORECASE)
            car['moc_km'] = int(moc_match.group(1)) if moc_match else 'Brak danych'
        else:
            car['moc_km'] = 'Brak danych'

        # --- Pojemność skokowa ---
        if subtitle_elem:
            subtitle_text = subtitle_elem.text.strip()
            pojemnosc_match = re.search(r'(\d+[\s\d]*\s*cm3)', subtitle_text)
            car['pojemnosc'] = pojemnosc_match.group(1) if pojemnosc_match else 'Brak danych'
        else:
            car['pojemnosc'] = 'Brak danych'

        # --- Dane techniczne ---
        params = listing.find_all('dd', {'data-parameter': True})
        car['przebieg'] = params[0].text.strip() if len(params) > 0 else 'Brak danych'
        car['paliwo'] = params[1].text.strip() if len(params) > 1 else 'Brak danych'
        car['skrzynia'] = params[2].text.strip() if len(params) > 2 else 'Brak danych'
        car['rok'] = params[3].text.strip() if len(params) > 3 else 'Brak danych'

        # --- Lokalizacja ---
        location_elem = listing.find('p', class_='ooa-oj1jk2')
        if location_elem and '(' in location_elem.text:
            location_text = location_elem.text.strip()
            parts = location_text.split('(')
            car['miasto'] = parts[0].strip()
            car['wojewodztwo'] = parts[1].replace(')', '').strip()
        else:
            car['miasto'] = car['wojewodztwo'] = 'Brak danych'

        # --- Typ sprzedawcy ---
        seller_elem = listing.find('li', class_='elb81bb5')
        if seller_elem and "Prywatny sprzedawca" in seller_elem.get_text():
            car['czy_prywatny'] = 1
        else:
            car['czy_prywatny'] = 0

        return car

    def scrape_brand_iteratively(self, brand):
        """Fallback method when page count detection fails"""
        base_url = f'https://www.otomoto.pl/osobowe/{brand}?search%5Border%5D=created_at_first%3Adesc'
        cars = []
        current_page = 1
        has_next_page = True

        with tqdm(desc=f"Scrapowanie {brand} (iteracyjnie)") as pbar:
            while has_next_page and current_page <= MAX_PAGES:
                try:
                    time.sleep(random.uniform(*DELAY_RANGE))
                    url = f"{base_url}&page={current_page}" if current_page > 1 else base_url
                    headers = {'User-Agent': self.get_random_user_agent()}

                    response = self.session.get(url, headers=headers, timeout=TIMEOUT)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Check for listings
                    listings = soup.find_all('article', {'data-sentry-component': 'AdCardWrapper'})
                    if not listings:
                        break

                    # Process listings
                    for listing in listings:
                        car = self.scrape_car_listing(listing, url)
                        cars.append(car)

                    # Save data
                    save_to_csv(cars, brand)
                    cars = []

                    # Check for next page
                    next_btn = soup.find('li', attrs={'aria-label': lambda x: x and 'next' in x.lower()})
                    has_next_page = bool(next_btn) and 'disabled' not in next_btn.get('class', [])

                    current_page += 1
                    pbar.update(1)

                except Exception as e:
                    print(f"Błąd podczas scrapowania strony {current_page}: {e}")
                    break

        return True

    def scrape_brand(self, brand):
        """Main scraping method with both approaches"""
        base_url = f'https://www.otomoto.pl/osobowe/{brand}?search%5Border%5D=created_at_first%3Adesc'
        cars = []

        # First try to detect page count
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            response = self.session.get(base_url, headers=headers, timeout=TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check if we got redirected to captcha
            if 'captcha' in response.url.lower():
                print("Wykryto captcha! Próbuję ponownie...")
                time.sleep(30)
                return self.scrape_brand_iteratively(brand)

            total_pages = self.get_page_count(soup)
        except Exception as e:
            print(f"Błąd wykrywania liczby stron: {e}")
            return self.scrape_brand_iteratively(brand)

        print(f"\nRozpoczynam scrapowanie marki {brand.upper()} (stron: {total_pages})")

        for page in tqdm(range(1, total_pages + 1), desc=f"Scrapowanie {brand}"):
            try:
                time.sleep(random.uniform(*DELAY_RANGE))
                url = f"{base_url}&page={page}" if page > 1 else base_url
                headers = {'User-Agent': self.get_random_user_agent()}

                response = self.session.get(url, headers=headers, timeout=TIMEOUT)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                listings = soup.find_all('article', {'data-sentry-component': 'AdCardWrapper'})

                for listing in listings:
                    car = self.scrape_car_listing(listing, url)
                    cars.append(car)

                # Save after each page
                save_to_csv(cars, brand)
                cars = []

            except Exception as e:
                print(f"Błąd podczas scrapowania strony {page}: {e}")
                continue

        return True