"""
Модуль настройки логирования для всех компонентов приложения.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logger(log_file="youtube_downloader.log", level=logging.INFO):
    """
    Настройка логирования для приложения.

    Args:
        log_file (str): Имя файла для логирования.
        level (int): Уровень логирования.
    """
    # Получение корневого логгера
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Очистка обработчиков, чтобы избежать дублирования логов
    logger.handlers.clear()
    
    # Создание форматтера для логов
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Создание обработчика для вывода в файл с ротацией
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Создание обработчика для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Установка уровня логирования для сторонних библиотек
    logging.getLogger('waitress').setLevel(logging.WARNING)
    logging.getLogger('flask').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Отключение логирования yt-dlp
    logging.getLogger('yt_dlp').setLevel(logging.CRITICAL)
    
    # Логирование информации о запуске
    logger.info("Logger initialized")