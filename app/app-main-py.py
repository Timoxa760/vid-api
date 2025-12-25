"""
VID-API: FastAPI application entry point
Основное приложение FastAPI для преобразования видео в ASCII
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from app.config import get_settings
from app.routes import convert, download, status, health, ws

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получить конфиг
settings = get_settings()

# Создать необходимые директории
Path(settings.UPLOADS_DIR).mkdir(exist_ok=True)
Path(settings.RESULTS_DIR).mkdir(exist_ok=True)
Path(settings.LOGS_DIR).mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("🚀 VID-API запущено")
    logger.info(f"📂 Директория для загрузок: {settings.UPLOADS_DIR}")
    logger.info(f"📂 Директория для результатов: {settings.RESULTS_DIR}")
    yield
    logger.info("🛑 VID-API останавливается")


# Создать приложение FastAPI
app = FastAPI(
    title="VID-API",
    description="REST API для преобразования видео в ASCII-анимацию",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Добавить CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключить маршруты
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(convert.router, prefix="/api/v1", tags=["Convert"])
app.include_router(download.router, prefix="/api/v1", tags=["Download"])
app.include_router(status.router, prefix="/api/v1", tags=["Status"])
app.include_router(ws.router, prefix="/api/v1", tags=["WebSocket"])


# Глобальный обработчик исключений
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Обработчик всех необработанных исключений"""
    logger.exception(f"Необработанное исключение: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.DEBUG else "Внутренняя ошибка сервера",
            "detail": str(exc) if settings.DEBUG else None,
        }
    )


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "name": "VID-API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
    )
