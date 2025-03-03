"""
Модуль для скачивания видео и аудио с YouTube.
Основан на классе YouTubeDownloader с элегантной структурой и минимальным логированием.
"""

import os
import logging
import re
import uuid
import glob
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from yt_dlp import YoutubeDL
import ffmpeg


class YouTubeDownloader:
    """Класс для скачивания видео и аудио с YouTube."""

    def __init__(self, download_dir, temp_dir, base_url):
        """
        Инициализация объекта YouTubeDownloader.

        Args:
            download_dir (str): Директория для сохранения загруженных файлов.
            temp_dir (str): Директория для временных файлов.
            base_url (str): Базовый URL для доступа к загруженным файлам.
        """
        self.download_dir = download_dir
        self.temp_dir = temp_dir
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def _sanitize_filename(self, filename):
        """
        Очистка имени файла от недопустимых символов.

        Args:
            filename (str): Исходное имя файла.

        Returns:
            str: Очищенное имя файла.
        """
        # Замена недопустимых символов
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Ограничение длины имени файла
        if len(filename) > 120:
            filename = filename[:120]
            
        return filename

    @staticmethod
    def _get_video_id(url):
        """
        Извлекает идентификатор видео из URL YouTube.

        Args:
            url (str): URL видео на YouTube.

        Returns:
            str: Идентификатор видео или None, если идентификатор не найден.
        """
        # Используем urlparse для разбора URL
        parsed_url = urlparse(url)

        # Проверяем, является ли URL корректным YouTube URL
        if parsed_url.netloc in ('www.youtube.com', 'youtube.com'):
            # Используем parse_qs для извлечения параметров запроса
            query_params = parse_qs(parsed_url.query)
            # Ищем параметр 'v', который содержит идентификатор видео
            video_id = query_params.get('v')
            if video_id:
                return video_id[0]

        # Если URL не соответствует ожидаемому формату, используем регулярное выражение
        match = re.search(r'(?<=v=)[\w-]+', url)
        if not match:
            match = re.search(r'(?<=be/)[\w-]+', url)
        if match:
            return match.group()

        return None

    def _validate_youtube_url(self, url):
        """
        Проверяет, является ли URL действительной ссылкой на YouTube видео.

        Args:
            url (str): URL для проверки.

        Returns:
            bool: True, если URL действителен, False в противном случае.
        """
        self.logger.info(f"Validating YouTube URL: {url}")
        
        video_id = self._get_video_id(url)
        if not video_id:
            self.logger.warning(f"Invalid YouTube URL format: {url}")
            return False
        
        try:
            with YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                if not info_dict:
                    self.logger.warning(f"Cannot extract info from YouTube URL: {url}")
                    return False
                return True
        except Exception as e:
            self.logger.error(f"Error validating YouTube URL {url}: {e}")
            return False

    def _get_video_info(self, url):
        """
        Получает информацию о видео с YouTube.

        Args:
            url (str): URL видео на YouTube.

        Returns:
            dict: Словарь с информацией о видео или None в случае ошибки.
        """
        self.logger.info(f"Getting video info for: {url}")
        try:
            with YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                self.logger.info(f"Retrieved video info: {info_dict.get('title', 'Unknown title')}")
                return info_dict
        except Exception as e:
            self.logger.error(f"Error getting video info from {url}: {e}")
            return None

    def _generate_output_filename(self, video_title, video_id, suffix="", extension=""):
        """
        Генерирует имя файла для сохранения.

        Args:
            video_title (str): Название видео.
            video_id (str): ID видео.
            suffix (str): Дополнительный суффикс для имени файла.
            extension (str): Расширение файла.

        Returns:
            str: Сгенерированное имя файла.
        """
        # Создаем уникальный идентификатор для файла
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        
        # Формируем имя файла
        sanitized_title = self._sanitize_filename(video_title)
        filename = f"{sanitized_title}_{video_id}"
        
        if suffix:
            filename += f"_{suffix}"
            
        filename += f"_{timestamp}_{unique_id}"
        
        if extension:
            if not extension.startswith('.'):
                extension = f".{extension}"
            filename += extension
            
        return filename

    def _download_stream(self, url, format_code, output_path):
        """
        Загружает один поток (видео или аудио) с YouTube.
        
        Args:
            url (str): URL видео на YouTube.
            format_code (str): Код формата для загрузки (например, 'bestvideo[height<=720]').
            output_path (str): Путь для сохранения файла.
            
        Returns:
            dict: Информация о загруженном файле или None в случае ошибки.
        """
        try:
            # Определяем тип потока для логов
            stream_type = "audio" if "audio" in format_code else "video"
            
            self.logger.info(f"Downloading {stream_type} stream")
            
            # Настраиваем опции для yt-dlp
            ydl_opts = {
                'format': format_code,
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'noprogress': True,  # Отключаем вывод прогресса
                # Сохраняем потоки в оригинальном формате без перекодирования
                'postprocessor_args': {
                    'ffmpeg': ['-c:v', 'copy', '-c:a', 'copy']
                }
            }
            
            # Выполняем загрузку
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                self.logger.info(f"{stream_type.capitalize()} stream downloaded")
                return info
                
        except Exception as e:
            self.logger.error(f"Error downloading {stream_type} from {url}: {e}")
            return None

    def _find_file_by_pattern(self, pattern):
        """
        Поиск файла по шаблону.
        
        Args:
            pattern (str): Шаблон для поиска файла.
            
        Returns:
            str: Путь к найденному файлу или None, если файл не найден.
        """
        files = glob.glob(pattern)
        if files:
            self.logger.debug(f"Found file with original extension: {files[0]}")
            return files[0]
        else:
            self.logger.warning(f"No files found matching pattern: {pattern}")
            return None

    def _merge_video_audio(self, video_path, audio_path, output_path):
        """
        Объединение видео и аудио в один файл с помощью ffmpeg.
        
        Args:
            video_path (str): Путь к видео файлу.
            audio_path (str): Путь к аудио файлу.
            output_path (str): Путь для сохранения объединенного файла.
            
        Returns:
            bool: True если объединение выполнено успешно, иначе False.
        """
        try:
            self.logger.info("Merging video and audio streams")
            
            # Проверяем существование файлов
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
                
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
                
            # Объединяем файлы с помощью ffmpeg
            ffmpeg.input(video_path).output(
                ffmpeg.input(audio_path),
                output_path,
                vcodec='copy',
                acodec='copy',
                loglevel='quiet'
            ).run(overwrite_output=True)
            
            # Удаляем временные файлы после успешного объединения
            os.remove(video_path)
            os.remove(audio_path)
            
            self.logger.info(f"Video and audio merged successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error merging video and audio: {e}")
            return False

    def download_video(self, url, resolution=720):
        """
        Загружает видео с YouTube в указанном разрешении.

        Args:
            url (str): URL видео на YouTube.
            resolution (int): Желаемое разрешение видео.

        Returns:
            dict: Информация о загруженном файле или None в случае ошибки.
                {
                    "local_path": "путь к файлу на сервере",
                    "url": "URL для доступа к файлу",
                    "title": "название видео",
                    "duration": "длительность в секундах"
                }
        """
        self.logger.info(f"Request to download video: {url} with resolution {resolution}p")
        
        if not self._validate_youtube_url(url):
            self.logger.error(f"Invalid YouTube URL: {url}")
            return None
            
        try:
            # Получение информации о видео
            info_dict = self._get_video_info(url)
            if not info_dict:
                return None
                
            video_title = info_dict.get('title', 'video')
            video_id = self._get_video_id(url)
            duration = info_dict.get('duration', 0)
            
            # Создаем имена временных файлов с маской для расширения
            temp_video_filename = f"{video_id}_video.%(ext)s"
            temp_audio_filename = f"{video_id}_audio.%(ext)s"
            
            temp_video_path = os.path.join(self.temp_dir, temp_video_filename)
            temp_audio_path = os.path.join(self.temp_dir, temp_audio_filename)
            
            # Формирование имени финального файла
            output_filename = self._generate_output_filename(video_title, video_id, f"{resolution}p", ".mkv")
            output_path = os.path.join(self.download_dir, output_filename)
            
            # Загрузка видео потока
            self._download_stream(url, f'bestvideo[height<={resolution}]', temp_video_path)
            
            # Загрузка аудио потока
            self._download_stream(url, 'bestaudio', temp_audio_path)
            
            # Поиск фактических файлов с их оригинальными расширениями
            video_pattern = os.path.join(self.temp_dir, f"{video_id}_video.*")
            audio_pattern = os.path.join(self.temp_dir, f"{video_id}_audio.*")
            
            video_file = self._find_file_by_pattern(video_pattern)
            audio_file = self._find_file_by_pattern(audio_pattern)
            
            if not video_file or not audio_file:
                raise FileNotFoundError("Could not find downloaded video or audio files")
                
            # Объединение видео и аудио
            merge_success = self._merge_video_audio(video_file, audio_file, output_path)
            
            if not merge_success:
                raise Exception("Failed to merge video and audio")
                
            # Формирование URL для доступа к файлу
            url_path = f"{self.base_url}/{output_filename}"
            
            self.logger.info(f"Video download complete: {output_path}")
            
            return {
                "local_path": output_path,
                "url": url_path,
                "title": video_title,
                "duration": duration
            }
            
        except Exception as e:
            self.logger.error(f"Error downloading video from {url}: {e}")
            return None

    def download_audio(self, url, convert_to_mp3=False):
        """
        Загружает только аудио с YouTube.

        Args:
            url (str): URL видео на YouTube.
            convert_to_mp3 (bool): Конвертировать в MP3 формат.

        Returns:
            dict: Информация о загруженном файле или None в случае ошибки.
                {
                    "local_path": "путь к файлу на сервере",
                    "url": "URL для доступа к файлу",
                    "title": "название видео",
                    "duration": "длительность в секундах"
                }
        """
        self.logger.info(f"Request to download audio: {url}, convert_to_mp3={convert_to_mp3}")
        
        if not self._validate_youtube_url(url):
            self.logger.error(f"Invalid YouTube URL: {url}")
            return None
            
        try:
            # Получение информации о видео
            info_dict = self._get_video_info(url)
            if not info_dict:
                return None
                
            video_title = info_dict.get('title', 'audio')
            video_id = self._get_video_id(url)
            duration = info_dict.get('duration', 0)
            
            # Формирование имени файла
            ext = ".mp3" if convert_to_mp3 else ".m4a"
            suffix = "mp3" if convert_to_mp3 else "audio"
            output_filename = self._generate_output_filename(video_title, video_id, suffix, ext)
            output_path = os.path.join(self.download_dir, output_filename)
            
            # Опции для скачивания
            format_code = 'bestaudio'
            
            if convert_to_mp3:
                self.logger.info("Starting audio download with MP3 conversion")
                
                # Сначала скачиваем аудио во временный файл с маской для расширения
                temp_audio_filename = f"{video_id}_audio.%(ext)s"
                temp_audio_path = os.path.join(self.temp_dir, temp_audio_filename)
                
                self._download_stream(url, format_code, temp_audio_path)
                
                # Находим фактический файл с оригинальным расширением
                audio_pattern = os.path.join(self.temp_dir, f"{video_id}_audio.*")
                audio_file = self._find_file_by_pattern(audio_pattern)
                
                if not audio_file:
                    raise FileNotFoundError("Could not find downloaded audio file")
                
                # Конвертируем в MP3
                self.logger.info("Converting audio to MP3")
                
                try:
                    ffmpeg.input(audio_file).output(output_path, format='mp3', acodec='libmp3lame', loglevel='quiet').run(overwrite_output=True)
                    
                    # Удаляем временный файл
                    os.remove(audio_file)
                    
                    self.logger.info("Audio converted to MP3 successfully")
                except Exception as e:
                    self.logger.error(f"Error converting to MP3: {e}")
                    return None
            else:
                # Прямая загрузка аудио без конвертации
                self._download_stream(url, format_code, output_path)
                
                # Находим фактический файл в случае, если yt-dlp добавил расширение
                output_pattern = f"{os.path.splitext(output_path)[0]}.*"
                actual_file = self._find_file_by_pattern(output_pattern)
                
                if actual_file:
                    output_path = actual_file
                else:
                    self.logger.warning(f"Could not find output audio file")
                    return None
            
            # Получаем только имя файла для URL
            filename = os.path.basename(output_path)
            url_path = f"{self.base_url}/{filename}"
            
            self.logger.info(f"Audio download complete: {output_path}")
            
            return {
                "local_path": output_path,
                "url": url_path,
                "title": video_title,
                "duration": duration
            }
            
        except Exception as e:
            self.logger.error(f"Error downloading audio from {url}: {e}")
            return None