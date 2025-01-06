import os
import logging
from datetime import datetime

LOG_DIR = 'logs'

log_timestamp = datetime.now().date().strftime("%Y%m%d%H%M%S")
log_file = os.path.join(LOG_DIR, f"tweet_logs_{log_timestamp}.log")


def setup_logging(log_file=log_file, level=logging.INFO)-> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger