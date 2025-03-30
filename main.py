from scraper.file_utils import create_directories, get_brands_from_file
from scraper.otomoto_scraper import OtomotoScraper
from utils.logger import setup_logger
import time
import random


def main():
    logger = setup_logger()
    logger.info("Rozpoczynanie scrapowania Otomoto")

    create_directories()
    brands = get_brands_from_file()

    if not brands:
        logger.warning("Brak marek do scrapowania w pliku input/brands.txt")
        return

    scraper = OtomotoScraper()

    for brand in brands:
        try:
            logger.info(f"Rozpoczynanie scrapowania marki: {brand}")
            scraper.scrape_brand(brand)
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            logger.error(f"Błąd podczas scrapowania marki {brand}: {str(e)}")
            continue

    logger.info("Scrapowanie zakończone")


if __name__ == '__main__':
    main()