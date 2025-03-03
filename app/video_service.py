"""
Сервис для обработки запросов на скачивание видео/аудио с YouTube.
Координирует работу downloader и формирует ответы API.
"""

import logging
import os
from datetime import datetime
import json
import threading
import time

from app.downloader import YouTubeDownloader


class VideoService:
    """Сервис для обработки запросов на скачивание видео с YouTube."""

    def __init__(self, config):
        """
        Инициализация сервиса для обработки запросов на скачивание.

        Args:
            config (dict): Конфигурация приложения.
        """
        self.config = config
        self.download_dir = config["downloader"]["download_dir"]
        self.base_url = config["downloader"]["base_url"]
        self.temp_dir = config["downloader"]["temp_dir"]
        self.default_resolution = config["downloader"]["default_resolution"]
        
        self.downloader = YouTubeDownloader(
            download_dir=self.download_dir,
            temp_dir=self.temp_dir,
            base_url=self.base_url
        )
        
        self.logger = logging.getLogger(__name__)
        

    def download_video(self, url, resolution=None):
        """
        Обрабатывает запрос на скачивание видео.

        Args:
            url (str): URL видео на YouTube.
            resolution (int, optional): Желаемое разрешение видео.

        Returns:
            tuple: (результат, код_ответа)
                результат: dict с информацией о скачанном файле или с ошибкой
                код_ответа: HTTP-код ответа
        """
        self.logger.info(f"Received request to download video: {url}")
        
        # Валидация URL
        if not url:
            return {"error": "URL is required"}, 400
            
        # Определение разрешения
        if resolution is None:
            resolution = self.default_resolution
        else:
            try:
                resolution = int(resolution)
                if resolution <= 0:
                    return {"error": "Resolution must be a positive integer"}, 400
            except ValueError:
                return {"error": "Resolution must be a valid integer"}, 400
        
        # Скачивание видео
        result = self.downloader.download_video(url, resolution)
        
        if result is None:
            return {"error": "Failed to download video"}, 500
            
        return result, 200

    def download_audio(self, url, convert_to_mp3=False):
        """
        Обрабатывает запрос на скачивание аудио.

        Args:
            url (str): URL видео на YouTube.
            convert_to_mp3 (bool): Конвертировать в MP3 формат.

        Returns:
            tuple: (результат, код_ответа)
                результат: dict с информацией о скачанном файле или с ошибкой код_ответа: HTTP-код ответа
        """
        self.logger.info(f"Received request to download audio: {url}, convert_to_mp3={convert_to_mp3}")
        
        # Валидация URL
        if not url:
            return {"error": "URL is required"}, 400
            
        # Скачивание аудио
        result = self.downloader.download_audio(url, convert_to_mp3)
        
        if result is None:
            return {"error": "Failed to download audio"}, 500
            
        return result, 200
