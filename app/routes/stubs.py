"""
Stub роуты для download, status и ws (WebSocket)
Реализованы в convert.py, здесь заглушки
"""

from fastapi import APIRouter

router = APIRouter()

# Все эндпоинты уже реализованы в convert.py
# Здесь остаются для возможности расширения

@router.get("/download/{job_id}")
async def list_downloads(job_id: str):
    """Список доступных файлов для скачивания"""
    return {"message": "Используйте /api/v1/download/{job_id}/{type}"}


@router.get("/status")
async def list_jobs():
    """Список всех задач"""
    return {"message": "Используйте /api/v1/status/{job_id}"}


@router.websocket("/ws/convert")
async def websocket_convert(websocket):
    """WebSocket для потоковой передачи кадров (в разработке)"""
    await websocket.accept()
    await websocket.send_json({"message": "WebSocket поддержка скоро будет доступна"})
    await websocket.close()
