"""
Маршруты API для YouTube Downloader Service.
"""

import logging
import json
import os
from flask import request, jsonify, Response, send_from_directory, current_app

from .video_service import VideoService


class Routes:
    """Класс для регистрации маршрутов API."""

    def __init__(self, app, config):
        """
        Инициализация маршрутов API.

        Args:
            app: Flask-приложение.
            config (dict): Конфигурация приложения.
        """
        self.app = app
        self.config = config
        self.video_service = VideoService(config)
        self.logger = logging.getLogger(__name__)

    def register_routes(self):
        """Регистрация всех маршрутов API."""
        # Web клиент
        self.app.route('/')(self.index)
        
        # Системные маршруты
        self.app.route('/health')(self.health)
        self.app.route('/config')(self.get_config)
        
        # Маршруты API
        self.app.route('/v1/youtube/download', methods=['GET', 'POST'])(self.download_video)
        self.app.route('/v1/youtube/download/audio', methods=['GET', 'POST'])(self.download_audio)
        self.app.route('/v1/youtube/download/audio/mp3', methods=['GET', 'POST'])(self.download_audio_mp3)
        
        self.logger.info("Routes registered")

    def index(self):
        """
        Корневой маршрут - отдаёт HTML клиент.

        Returns:
            HTML-страница клиента.
        """
        self.logger.info("Serving web client")
        return current_app.send_static_file('index.html')

    def health(self):
        """
        Проверка статуса сервиса.

        Returns:
            JSON: Статус сервиса.
        """
        return jsonify({
            "status": "ok",
            "service": "youtube-downloader-api"
        })

    def get_config(self):
        """
        Получение текущей конфигурации сервиса (без секретных данных).

        Returns:
            JSON: Конфигурация сервиса.
        """
        # Удаляем из конфигурации секретные данные
        safe_config = {
            "server": {
                "host": self.config["server"]["host"],
                "port": self.config["server"]["port"]
            },
            "downloader": {
                "base_url": self.config["downloader"]["base_url"],
                "default_resolution": self.config["downloader"]["default_resolution"]
            },
            "api": {
                "rate_limit": self.config["api"]["rate_limit"]["enabled"]
            }
        }
        
        return jsonify(safe_config)

    def _get_url_from_request(self):
        """
        Извлекает URL из запроса (GET или POST).

        Returns:
            str: URL видео или None, если URL не найден.
        """
        if request.method == 'GET':
            return request.args.get('url')
        else:  # POST
            if request.is_json:
                return request.json.get('url')
            else:
                return request.form.get('url')

    def download_video(self):
        """
        Маршрут для скачивания видео.

        Returns:
            JSON: Результат скачивания.
        """
        url = self._get_url_from_request()
        
        # Получение разрешения из запроса
        resolution = None
        if request.method == 'GET':
            resolution = request.args.get('resolution')
        else:  # POST
            if request.is_json:
                resolution = request.json.get('resolution')
            else:
                resolution = request.form.get('resolution')
                
        # Скачивание видео
        result, status_code = self.video_service.download_video(url, resolution)
        
        return jsonify(result), status_code

    def download_audio(self):
        """
        Маршрут для скачивания аудио в оригинальном формате.

        Returns:
            JSON: Результат скачивания.
        """
        url = self._get_url_from_request()
        
        # Скачивание аудио
        result, status_code = self.video_service.download_audio(url, convert_to_mp3=False)
        
        return jsonify(result), status_code

    def download_audio_mp3(self):
        """
        Маршрут для скачивания аудио в формате MP3.

        Returns:
            JSON: Результат скачивания.
        """
        url = self._get_url_from_request()
        
        # Скачивание аудио и конвертация в MP3
        result, status_code = self.video_service.download_audio(url, convert_to_mp3=True)
        
        return jsonify(result), status_code