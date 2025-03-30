import os
import csv
from pathlib import Path
from scraper.config import INPUT_DIR, OUTPUT_DIR


def create_directories():
    """Tworzy potrzebne katalogi jeśli nie istnieją"""
    Path(INPUT_DIR).mkdir(exist_ok=True)
    Path(OUTPUT_DIR).mkdir(exist_ok=True)


def get_brands_from_file():
    """Wczytuje marki z pliku input/brands.txt"""
    brands_file = os.path.join(INPUT_DIR, 'brands.txt')
    with open(brands_file, 'r', encoding='utf-8') as f:
        brands = [line.strip() for line in f if line.strip()]
    return brands


def save_to_csv(cars, brand):
    """Zapisuje dane do pliku CSV w katalogu output"""
    filename = os.path.join(OUTPUT_DIR, f'otomoto_{brand}.csv')
    fieldnames = [
        'marka', 'model', 'opis', 'cena', 'moc_km', 'przebieg', 'paliwo',
        'skrzynia', 'rok', 'pojemnosc', 'miasto', 'wojewodztwo', 'czy_prywatny', 'link'
    ]

    mode = 'a' if os.path.exists(filename) else 'w'
    with open(filename, mode=mode, encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if mode == 'w':
            writer.writeheader()
        writer.writerows(cars)