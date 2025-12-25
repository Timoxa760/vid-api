"""

API роуты для конвертации видео в ASCII

"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
import logging
import uuid
import tempfile
from pathlib import Path
from datetime import datetime
import asyncio

from app.config import get_settings
from app.models import ConvertRequest, ConvertResponse, JobStatus
from vid_core.converter import ASCIIConverter, ConvertConfig
from vid_core.utils import ensure_dir, sanitize_filename

logger = logging.getLogger(__name__)

router = APIRouter()

settings = get_settings()

# In-memory хранилище статусов задач (в production использовать Redis)
JOBS_STATUS = {}

def create_job_id() -> str:
    """Создать уникальный ID задачи"""
    return str(uuid.uuid4())[:8]

@router.post("/convert/video", response_model=ConvertResponse)
async def convert_video(
    file: UploadFile = File(...),
    width: int = Form(120),
    style: str = Form("normal"),
    save_txt: bool = Form(False),
    save_png: bool = Form(True),
    save_mp4: bool = Form(True),
    brightness: float = Form(1.0),
    contrast: float = Form(1.0),
    gamma: float = Form(1.0),
    random_colors: bool = Form(False),
    transparent_bg: bool = Form(False),
    bg_color: str = Form("#000000"),
    text_color: str = Form("#00FF00"),
    fps: int = Form(30),
    crf: int = Form(23),
    resolution: str = Form("high"),
    background_tasks: BackgroundTasks = None,
):
    """
    Конвертировать видео в ASCII-анимацию

    - **file**: Видеофайл (MP4, AVI, MOV, MKV и т.д.)
    - **width**: Ширина ASCII-кадра (10-240)
    - **style**: Стиль ASCII (normal, inverted, dots, gradient, blocks)
    - **save_txt**: Сохранять текстовые кадры
    - **save_png**: Сохранять PNG-кадры
    - **save_mp4**: Собрать MP4-видео
    - **brightness**: Коррекция яркости (0.5-2.0)
    - **contrast**: Коррекция контраста (0.5-2.0)
    - **gamma**: Гамма-коррекция (0.5-2.0)
    - **random_colors**: Случайные цвета
    - **transparent_bg**: Прозрачный фон
    - **bg_color**: HEX-цвет фона (#000000)
    - **text_color**: HEX-цвет текста (#00FF00)
    - **fps**: FPS для видео
    - **crf**: Quality (0-51)
    - **resolution**: Разрешение (low, medium, high, 4k)
    """
    job_id = create_job_id()
    start_time = datetime.utcnow()
    logger.info(f"Начата задача {job_id}: {file.filename}")

    # Обновить статус
    JOBS_STATUS[job_id] = {
        "status": "processing",
        "progress": 0.0,
        "message": "Загрузка файла...",
        "started_at": start_time,
    }

    try:
        # Проверить размер файла
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Файл слишком большой: {file_size_mb:.1f}MB > {settings.MAX_FILE_SIZE}MB"
            )

        # Создать временный файл
        temp_dir = Path(tempfile.gettempdir()) / f"vid_api_{job_id}"
        ensure_dir(str(temp_dir))
        input_path = temp_dir / sanitize_filename(file.filename)
        with open(input_path, 'wb') as f:
            f.write(content)
        logger.info(f"Файл загружен: {input_path} ({file_size_mb:.1f}MB)")

        # Обновить статус
        JOBS_STATUS[job_id]["message"] = "Инициализация конвертера..."
        JOBS_STATUS[job_id]["progress"] = 0.1

        # Создать конфиг
        config = ConvertConfig(
            width=width,
            style=style,
            brightness=brightness,
            contrast=contrast,
            gamma=gamma,
            random_colors=random_colors,
            transparent_bg=transparent_bg,
            bg_color=bg_color,
            text_color=text_color,
            fps=fps,
            crf=crf,
            save_txt=save_txt,
            save_png=save_png,
            save_mp4=save_mp4,
            resolution=resolution,
        )

        # Создать конвертер
        output_dir = Path(settings.RESULTS_DIR) / job_id
        ensure_dir(str(output_dir))
        converter = ASCIIConverter(str(output_dir), config)

        # Функция для отчёта о прогрессе
        def progress_callback(progress: float, frame_num: int, total: int):
            JOBS_STATUS[job_id]["progress"] = 0.1 + progress * 0.8
            JOBS_STATUS[job_id]["message"] = f"Обработано {frame_num}/{total} кадров"
            JOBS_STATUS[job_id]["frames_processed"] = frame_num
            JOBS_STATUS[job_id]["total_frames"] = total

        # Выполнить конвертацию
        result = converter.convert_video(str(input_path), progress_callback)

        # Обновить статус
        JOBS_STATUS[job_id]["status"] = "completed"
        JOBS_STATUS[job_id]["progress"] = 1.0
        JOBS_STATUS[job_id]["message"] = "Готово"
        
        # ✅ ИСПРАВЛЕНО: проверяем "mp4_file" вместо "mp4_path"
        JOBS_STATUS[job_id]["result"] = {
            "frames_count": result["frames_count"],
            "fps": result["fps"],
            "mp4_file": result.get("mp4_file"),  # Это ключ из converter.py
            "txt_files_count": result.get("txt_files_count", 0),
            "png_files_count": result.get("png_files_count", 0),
        }

        # Очистить временные файлы (опционально)
        if background_tasks:
            background_tasks.add_task(cleanup_temp, str(temp_dir))

        logger.info(f"Задача {job_id} завершена успешно")
        elapsed = (datetime.utcnow() - start_time).total_seconds()

        return ConvertResponse(
            job_id=job_id,
            status="completed",
            message="Конвертация завершена успешно",
            result=JOBS_STATUS[job_id]["result"],
            processing_time_seconds=elapsed,
            started_at=start_time,
            completed_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Ошибка в задаче {job_id}: {str(e)}", exc_info=True)
        JOBS_STATUS[job_id]["status"] = "failed"
        JOBS_STATUS[job_id]["error"] = str(e)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка конвертации: {str(e)}"
        )

@router.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Получить статус задачи"""
    if job_id not in JOBS_STATUS:
        raise HTTPException(
            status_code=404,
            detail=f"Задача {job_id} не найдена"
        )

    job = JOBS_STATUS[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0.0),
        message=job.get("message", ""),
        eta_seconds=None,
        frames_processed=job.get("frames_processed"),
        total_frames=job.get("total_frames"),
        error=job.get("error"),
    )

@router.get("/download/{job_id}/video")
async def download_video(job_id: str):
    """Скачать MP4 видео"""
    if job_id not in JOBS_STATUS:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if JOBS_STATUS[job_id]["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Задача еще не завершена: {JOBS_STATUS[job_id]['status']}"
        )

    output_dir = Path(settings.RESULTS_DIR) / job_id
    video_path = output_dir / "ascii_video.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="MP4 видео не найдено")

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=f"ascii_video_{job_id}.mp4"
    )

@router.get("/download/{job_id}/frames")
async def download_frames(job_id: str, format: str = "png"):
    """Скачать все кадры в ZIP"""
    if job_id not in JOBS_STATUS:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    import zipfile
    import io

    output_dir = Path(settings.RESULTS_DIR) / job_id

    # Найти кадры нужного формата
    if format == "png":
        frame_files = sorted(output_dir.glob("frame_*.png"))
        ext = ".png"
    elif format == "txt":
        frame_files = sorted(output_dir.glob("frame_*.txt"))
        ext = ".txt"
    else:
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат")

    if not frame_files:
        raise HTTPException(status_code=404, detail=f"Кадры формата {format} не найдены")

    # Создать ZIP в памяти
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for frame_file in frame_files:
            zf.write(frame_file, arcname=frame_file.name)

    zip_buffer.seek(0)

    return FileResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        filename=f"ascii_frames_{job_id}_{format}.zip"
    )

async def cleanup_temp(temp_dir: str):
    """Очистить временную директорию"""
    import shutil
    try:
        shutil.rmtree(temp_dir)
        logger.debug(f"Очищена временная директория: {temp_dir}")
    except Exception as e:
        logger.error(f"Ошибка при очистке {temp_dir}: {str(e)}")
