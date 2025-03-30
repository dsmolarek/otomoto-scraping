import logging
import os
from datetime import datetime
from pathlib import Path
from scraper.config import BASE_DIR


def setup_logger():
    """Konfiguracja systemu logowania"""
    logs_dir = os.path.join(BASE_DIR, 'logs')
    Path(logs_dir).mkdir(exist_ok=True)

    log_file = os.path.join(logs_dir, f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger('otomoto_scraper')