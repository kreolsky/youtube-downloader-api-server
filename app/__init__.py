"""
Основной модуль YouTube Downloader API Service.
Содержит класс YouTubeDownloaderAPI для инициализации и запуска сервиса.
"""

import os
import json
import logging
from waitress import serve
import flask
from flask import Flask
from flask_cors import CORS

from .utils import setup_logger
from .routes import Routes


class YouTubeDownloaderAPI:
    """Основной класс приложения YouTube Downloader API."""

    def __init__(self, config_path="config.json"):
        """
        Инициализация сервиса.

        Args:
            config_path (str): Путь к файлу конфигурации.
        """
        # Загрузка конфигурации
        self.config = self._load_config(config_path)
        
        # Настройка логгера
        setup_logger(self.config["downloader"]["log_file"])
        self.logger = logging.getLogger(__name__)
        
        # Создание директорий для загрузок и временных файлов
        self._create_directories()
        
        # Инициализация Flask-приложения
        self.app = Flask(__name__, 
                         static_folder=os.path.join(os.path.dirname(__file__), 'static'),
                         static_url_path='/static')
        
        # Настройка статической директории для загрузок
        self.app.add_url_rule(
            '/media/<path:filename>',
            'media_files',
            self._serve_media_files
        )
        
        # Настройка CORS
        CORS(self.app, origins=self.config["api"]["cors_origin"])
        
        # Регистрация маршрутов
        Routes(self.app, self.config).register_routes()
        
        self.logger.info("YouTube Downloader API Service initialized")

    def _load_config(self, config_path):
        """
        Загрузка и валидация конфигурации.

        Args:
            config_path (str): Путь к файлу конфигурации.

        Returns:
            dict: Загруженная конфигурация.
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            raise ValueError(f"Config file not found: {config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in config file: {config_path}")

    def _create_directories(self):
        """Создание необходимых директорий для работы сервиса."""
        download_dir = self.config["downloader"]["download_dir"]
        temp_dir = self.config["downloader"]["temp_dir"]
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        
        for directory in [download_dir, temp_dir, static_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f"Created directory: {directory}")

    def _serve_media_files(self, filename):
        """
        Обслуживание медиафайлов из директории загрузок.
        
        Args:
            filename (str): Имя запрашиваемого файла.
            
        Returns:
            Response: Flask-ответ с файлом.
        """
        download_dir = self.config["downloader"]["download_dir"]
        return flask.send_from_directory(download_dir, filename)

    def run(self):
        """Запуск сервера с помощью Waitress."""
        host = self.config["server"]["host"]
        port = self.config["server"]["port"]
        workers = self.config["server"]["workers"]
        
        self.logger.info(f"Starting YouTube Downloader API Service on {host}:{port}")
        
        # Запуск сервера с помощью Waitress
        serve(self.app, host=host, port=port, threads=workers)


def create_app(config_path="config.json"):
    """
    Создание и инициализация приложения.
    
    Args:
        config_path (str): Путь к файлу конфигурации.
        
    Returns:
        Flask: Инициализированное Flask-приложение.
    """
    api = YouTubeDownloaderAPI(config_path)
    return api.app
