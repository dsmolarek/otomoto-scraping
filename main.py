import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urljoin
import re


def scrape_otomoto(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    listings = soup.find_all('article', {'data-sentry-component': 'AdCardWrapper'})

    cars = []

    for listing in listings:
        car = {}

        # --- Tytuł i link ---
        title_elem = listing.find('h2', {'data-sentry-element': 'Title'})
        if title_elem:
            full_title = title_elem.text.strip()

            # Rozdziel markę, model i opis
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
            # Szukamy wzorca typu "258 KM" lub "258KM"
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

        cars.append(car)

    return cars


def save_to_csv(cars, filename='otomoto_bmw.csv'):
    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=[
            'marka', 'model', 'opis', 'cena', 'moc_km', 'przebieg', 'paliwo',
            'skrzynia', 'rok', 'pojemnosc', 'miasto', 'wojewodztwo', 'czy_prywatny', 'link'
        ])
        writer.writeheader()
        writer.writerows(cars)


if __name__ == '__main__':
    url = 'https://www.otomoto.pl/osobowe/bmw?search%5Border%5D=created_at_first%3Adesc&page=2'
    cars = scrape_otomoto(url)
    save_to_csv(cars)
    print(f'Zapisano {len(cars)} ogłoszeń do pliku otomoto_bmw.csv')