#!/usr/bin/env python3
"""
Точка входа для YouTube Downloader API Service.
Инициализирует и запускает сервис.
"""

import sys
import os
import argparse

from app import YouTubeDownloaderAPI


def main():
    """
    Основная функция для запуска YouTube Downloader API Service.
    Обрабатывает аргументы командной строки и запускает сервис.
    """
    parser = argparse.ArgumentParser(description="YouTube Downloader API Service")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.json", 
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Проверка существования конфигурационного файла
    if not os.path.exists(args.config):
        print(f"Error: Configuration file not found: {args.config}")
        sys.exit(1)
    
    try:
        # Инициализация и запуск сервиса
        api = YouTubeDownloaderAPI(args.config)
        api.run()
    except Exception as e:
        print(f"Error starting YouTube Downloader API Service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()