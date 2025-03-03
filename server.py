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
        
        # Проверка существования index.html в static директории
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        index_file = os.path.join(static_dir, 'index.html')
        
        if not os.path.exists(index_file):
            print(f"Warning: Web client file not found: {index_file}")
            print("The root endpoint (/) will not serve the web client.")
        
        api.run()
    except Exception as e:
        print(f"Error starting YouTube Downloader API Service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
