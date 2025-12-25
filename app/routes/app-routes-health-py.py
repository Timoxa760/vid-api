"""
Health check роуты
"""

from fastapi import APIRouter
from datetime import datetime
import logging

from app.config import get_settings
from app.models import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()

settings = get_settings()

# Время запуска сервера
START_TIME = datetime.utcnow()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Проверка здоровья сервера
    
    Возвращает статус сервера и основную информацию
    """
    uptime = (datetime.utcnow() - START_TIME).total_seconds()
    
    return HealthResponse(
        status="healthy",
        version=settings.PROJECT_VERSION,
        uptime_seconds=uptime,
        active_jobs=0,  # TODO: получить из job manager
        timestamp=datetime.utcnow(),
    )


@router.get("/version")
async def get_version():
    """Получить версию API"""
    return {
        "version": settings.PROJECT_VERSION,
        "project": settings.PROJECT_NAME,
        "timestamp": datetime.utcnow(),
    }


@router.get("/config")
async def get_config():
    """Получить публичную конфигурацию"""
    return {
        "supported_styles": settings.ASCII_STYLES,
        "max_file_size_mb": settings.MAX_FILE_SIZE,
        "max_width": 240,
        "min_width": 10,
        "default_fps": settings.DEFAULT_FPS,
        "default_crf": settings.DEFAULT_CRF,
    }
