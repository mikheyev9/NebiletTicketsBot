import os
import logging
from logging.handlers import TimedRotatingFileHandler

# Настройка логгера
logger = logging.getLogger("checkeventsbot")
logger.setLevel(logging.INFO)
log_dir = os.path.join(os.path.dirname(__file__), 'checkevents.log')
# Обработчик для записи логов в файл с ротацией каждые 5 дней
file_handler = TimedRotatingFileHandler(log_dir,
                                        when="D",
                                        interval=5,
                                        backupCount=0)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)