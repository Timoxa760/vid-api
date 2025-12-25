"""
Pydantic модели для API запросов и ответов
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class StyleEnum(str, Enum):
    """Доступные ASCII стили"""
    NORMAL = "normal"
    INVERTED = "inverted"
    DOTS = "dots"
    GRADIENT = "gradient"
    BLOCKS = "blocks"


class ConvertRequest(BaseModel):
    """Модель запроса для конвертации видео"""
    
    width: int = Field(120, ge=10, le=240, description="Ширина ASCII-кадра")
    style: StyleEnum = Field("normal", description="Стиль ASCII")
    save_txt: bool = Field(False, description="Сохранять текстовые кадры")
    save_png: bool = Field(True, description="Сохранять PNG-кадры")
    save_mp4: bool = Field(True, description="Собрать MP4-видео")
    
    brightness: float = Field(1.0, ge=0.5, le=2.0, description="Коррекция яркости")
    contrast: float = Field(1.0, ge=0.5, le=2.0, description="Коррекция контраста")
    gamma: float = Field(1.0, ge=0.5, le=2.0, description="Гамма-коррекция")
    
    random_colors: bool = Field(False, description="Случайные цвета")
    transparent_bg: bool = Field(False, description="Прозрачный фон")
    bg_color: str = Field("#000000", description="HEX-цвет фона")
    text_color: str = Field("#00FF00", description="HEX-цвет текста")
    
    fps: int = Field(30, ge=1, le=60, description="FPS для видео")
    crf: int = Field(23, ge=0, le=51, description="Quality (0=lossless, 51=worst)")
    
    @field_validator('bg_color', 'text_color')
    @classmethod
    def validate_hex_color(cls, v):
        """Валидировать HEX цвета"""
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Цвет должен быть в формате #XXXXXX')
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError('Некорректное HEX значение цвета')
        return v


class ConvertResponse(BaseModel):
    """Модель ответа конвертации"""
    
    job_id: str = Field(..., description="ID задачи")
    status: str = Field(..., description="Статус обработки")
    message: str = Field("", description="Сообщение")
    result: Optional[Dict[str, Any]] = Field(None, description="Результаты")
    processing_time_seconds: Optional[float] = Field(None, description="Время обработки")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobStatus(BaseModel):
    """Модель статуса задачи"""
    
    job_id: str = Field(..., description="ID задачи")
    status: str = Field(..., description="Статус (processing/completed/failed)")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Прогресс (0-1)")
    message: str = Field("", description="Сообщение статуса")
    eta_seconds: Optional[float] = Field(None, description="Оставшееся время")
    frames_processed: Optional[int] = Field(None, description="Обработано кадров")
    total_frames: Optional[int] = Field(None, description="Всего кадров")
    error: Optional[str] = Field(None, description="Текст ошибки")


class HealthResponse(BaseModel):
    """Модель ответа health check"""
    
    status: str = Field("healthy", description="Статус сервера")
    version: str = Field(..., description="Версия API")
    uptime_seconds: float = Field(..., description="Время работы")
    active_jobs: int = Field(..., description="Активных задач")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchConvertRequest(BaseModel):
    """Модель для пакетной конвертации"""
    
    files_count: int = Field(..., ge=1, le=100, description="Количество файлов")
    config: ConvertRequest = Field(..., description="Конфигурация конвертации")


class BatchConvertResponse(BaseModel):
    """Модель ответа пакетной конвертации"""
    
    batch_id: str = Field(..., description="ID батча")
    job_ids: List[str] = Field(..., description="IDs задач")
    status: str = Field(..., description="Статус батча")
    total: int = Field(..., description="Всего файлов")
    completed: int = Field(0, description="Завершено файлов")
    failed: int = Field(0, description="Ошибок")


class WebSocketMessage(BaseModel):
    """Модель сообщения WebSocket"""
    
    action: str = Field(..., description="Действие (start/progress/complete/error)")
    frame_number: Optional[int] = Field(None, description="Номер кадра")
    ascii_text: Optional[str] = Field(None, description="ASCII текст кадра")
    timestamp: Optional[float] = Field(None, description="Время в видео")
    progress: Optional[float] = Field(None, description="Прогресс")
    error: Optional[str] = Field(None, description="Ошибка")
    data: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные")


class ErrorResponse(BaseModel):
    """Модель ошибки"""
    
    error: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Сообщение ошибки")
    detail: Optional[str] = Field(None, description="Деталь ошибки")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FileInfo(BaseModel):
    """Информация о файле"""
    
    filename: str = Field(..., description="Имя файла")
    size_bytes: int = Field(..., description="Размер в байтах")
    created_at: datetime = Field(..., description="Время создания")
    url: str = Field(..., description="URL для скачивания")
