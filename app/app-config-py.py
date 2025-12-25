"""
Конфигурация приложения на основе переменных окружения
"""

from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path
import os


class Settings(BaseSettings):
    """Основные настройки приложения"""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    DEBUG: bool = False
    
    # Paths
    UPLOADS_DIR: str = "./uploads"
    RESULTS_DIR: str = "./results"
    LOGS_DIR: str = "./logs"
    MAX_FILE_SIZE: int = 500  # MB
    
    # Processing
    MAX_CONCURRENT_JOBS: int = 4
    JOB_TIMEOUT: int = 600  # seconds
    CLEANUP_AFTER: int = 24  # hours
    KEEP_FAILED_JOBS: bool = True
    
    # Video defaults
    DEFAULT_FPS: int = 30
    DEFAULT_CRF: int = 23
    DEFAULT_WIDTH: int = 120
    DEFAULT_STYLE: str = "normal"
    
    # ASCII styles
    ASCII_STYLES: List[str] = [
        "normal",
        "inverted",
        "dots",
        "gradient",
        "blocks"
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/vid-api.log"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "VID-API"
    PROJECT_VERSION: str = "1.0.0"
    
    # Redis (опционально)
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False
    
    # FFmpeg
    FFMPEG_PATH: str = "ffmpeg"
    FFMPEG_TIMEOUT: int = 300
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Синглтон для получения настроек
_settings = None


def get_settings() -> Settings:
    """Получить экземпляр конфигурации"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    """Перезагрузить конфигурацию"""
    global _settings
    _settings = Settings()
