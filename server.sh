#!/bin/bash
# Скрипт для запуска YouTube Downloader API Service

# Обработка аргументов
UPDATE_ENV=false
CONFIG_PATH="config.json"

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --update)
            UPDATE_ENV=true
            shift
            ;;
        --config)
            CONFIG_PATH="$2"
            shift
            shift
            ;;
        *)
            echo "Unknown option: $key"
            echo "Usage: ./server.sh [--update] [--config path/to/config.json]"
            exit 1
            ;;
    esac
done

# Проверка наличия conda
if ! command -v conda &> /dev/null; then
    echo "Error: conda is not installed or not available in PATH"
    exit 1
fi

# Имя окружения conda
ENV_NAME="youtube-downloader"

# Проверка существования окружения
if ! conda env list | grep -q "^$ENV_NAME "; then
    echo "Creating conda environment: $ENV_NAME"
    conda create -y -n $ENV_NAME python=3.12
    UPDATE_ENV=true
fi

# Обновление окружения при необходимости
if [ "$UPDATE_ENV" = true ]; then
    echo "Updating conda environment: $ENV_NAME"
    conda run -n $ENV_NAME pip install -r requirements.txt
fi

# Проверка наличия ffmpeg
if ! conda run -n $ENV_NAME command -v ffmpeg &> /dev/null; then
    echo "Installing ffmpeg in conda environment"
    conda install -y -n $ENV_NAME -c conda-forge ffmpeg
fi

# Проверка наличия конфигурационного файла
if [ ! -f "$CONFIG_PATH" ]; then
    echo "Error: Configuration file not found: $CONFIG_PATH"
    exit 1
fi

# Создание директорий для загрузок
DOWNLOAD_DIR=$(grep -o '"download_dir"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_PATH" | sed 's/"download_dir"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')
TEMP_DIR=$(grep -o '"temp_dir"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_PATH" | sed 's/"temp_dir"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')

mkdir -p "$DOWNLOAD_DIR" "$TEMP_DIR"

# Запуск сервера
echo "Starting YouTube Downloader API Service with config: $CONFIG_PATH"
conda run -n $ENV_NAME python server.py --config "$CONFIG_PATH"
