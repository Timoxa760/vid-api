"""
Утилиты для работы с цветами, путями и другие вспомогательные функции
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Tuple, Optional
import re

logger = logging.getLogger(__name__)


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Преобразовать HEX цвет в RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Преобразовать RGB в HEX"""
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])


def hex_to_bgr(hex_color: str) -> Tuple[int, int, int]:
    """Преобразовать HEX в BGR (для OpenCV)"""
    r, g, b = hex_to_rgb(hex_color)
    return (b, g, r)


def is_valid_hex_color(color: str) -> bool:
    """Проверить, является ли строка корректным HEX цветом"""
    pattern = r'^#[0-9a-fA-F]{6}$'
    return bool(re.match(pattern, color))


def ensure_dir(path: str) -> Path:
    """Создать директорию, если её нет"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_remove_dir(path: str) -> bool:
    """Безопасно удалить директорию"""
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
            logger.debug(f"Удалена директория: {path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при удалении директории {path}: {str(e)}")
        return False


def get_file_size_mb(file_path: str) -> float:
    """Получить размер файла в МБ"""
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception as e:
        logger.error(f"Ошибка при получении размера файла {file_path}: {str(e)}")
        return 0.0


def sanitize_filename(filename: str) -> str:
    """Санитизировать имя файла"""
    # Заменить недопустимые символы
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    # Заменить множественные подчёркивания на одно
    sanitized = re.sub(r'_+', '_', sanitized)
    # Удалить ведущие/завершающие подчёркивания
    sanitized = sanitized.strip('_')
    return sanitized


def get_frame_filename(frame_number: int, extension: str = ".txt") -> str:
    """Получить имя файла кадра"""
    return f"frame_{frame_number:06d}{extension}"


def get_video_filename(extension: str = ".mp4") -> str:
    """Получить имя файла видео"""
    return f"ascii_video{extension}"


def format_seconds(seconds: float) -> str:
    """Форматировать время в удобный вид"""
    if seconds < 1:
        return f"{seconds:.2f}s"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_file_size(size_bytes: int) -> str:
    """Форматировать размер файла в удобный вид"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def validate_image_path(path: str) -> bool:
    """Проверить, существует ли файл изображения"""
    if not os.path.exists(path):
        logger.warning(f"Файл не существует: {path}")
        return False
    
    if not os.path.isfile(path):
        logger.warning(f"Путь не является файлом: {path}")
        return False
    
    return True


def get_safe_output_path(base_dir: str, filename: str) -> str:
    """Получить безопасный выходной путь (защита от path traversal)"""
    base = Path(base_dir).resolve()
    target = (base / sanitize_filename(filename)).resolve()
    
    # Проверить, что target находится внутри base
    if not str(target).startswith(str(base)):
        raise ValueError(f"Path traversal detected: {filename}")
    
    return str(target)


def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """Удалить старые файлы из директории"""
    import time
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0
    
    try:
        for file_path in Path(directory).glob('**/*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Удалён старый файл: {file_path}")
    except Exception as e:
        logger.error(f"Ошибка при очистке старых файлов: {str(e)}")
    
    return deleted_count
