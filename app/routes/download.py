from pathlib import Path
import logging
import io
import zipfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["download"])

settings = get_settings()


def get_job_dir(job_id: str) -> Path:
    """Директория с результатами для указанного job_id."""
    return Path(settings.RESULTS_DIR) / job_id


@router.get("/download/{job_id}/video")
async def download_video(job_id: str):
    """
    Скачать готовое MP4 видео ascii_video.mp4 для задачи.

    Используется фронтом для кнопки «Скачать MP4».
    """
    job_dir = get_job_dir(job_id)
    video_path = job_dir / "ascii_video.mp4"

    if not video_path.exists():
        logger.warning(f"MP4 not found for job {job_id}: {video_path}")
        raise HTTPException(status_code=404, detail="MP4 видео не найдено")

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"ascii_video_{job_id}.mp4",
    )


@router.get("/download/{job_id}/frame/{index}")
async def download_frame(job_id: str, index: int = 0):
    """
    Скачать отдельный PNG‑кадр по индексу.

    Примеры:
      GET /api/v1/download/abcd1234/frame/0   -> frame_000000.png
      GET /api/v1/download/abcd1234/frame/15  -> frame_000015.png

    Фронт берёт тут кадр предпросмотра.
    """
    if index < 0:
        raise HTTPException(status_code=400, detail="index must be >= 0")

    job_dir = get_job_dir(job_id)
    frame_path = job_dir / f"frame_{index:06d}.png"

    if not frame_path.exists():
        logger.warning(f"Frame not found for job {job_id}, index={index}: {frame_path}")
        raise HTTPException(status_code=404, detail="Кадр не найден")

    return FileResponse(
        path=str(frame_path),
        media_type="image/png",
        filename=f"ascii_frame_{job_id}_{index:06d}.png",
    )


@router.get("/download/{job_id}/frames")
async def download_frames_archive(job_id: str, format: str = "png"):
    """
    Скачать все кадры в формате PNG или TXT в виде ZIP архива.

    Примеры:
      GET /api/v1/download/abcd1234/frames?format=png
      GET /api/v1/download/abcd1234/frames?format=txt
    """
    job_dir = get_job_dir(job_id)

    if format == "png":
        pattern = "frame_*.png"
    elif format == "txt":
        pattern = "frame_*.txt"
    else:
        raise HTTPException(status_code=400, detail="Поддерживаются только форматы png или txt")

    frame_files = sorted(job_dir.glob(pattern))
    if not frame_files:
        logger.warning(f"No frames found for job {job_id} with format={format}")
        raise HTTPException(status_code=404, detail=f"Кадры формата {format} не найдены")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for frame_file in frame_files:
            zf.write(frame_file, arcname=frame_file.name)

    zip_buffer.seek(0)

    # В FileResponse можно передать file-like объект через path=zip_buffer,
    # FastAPI/Starlette корректно его отдаст
    return FileResponse(
        path=zip_buffer,
        media_type="application/zip",
        filename=f"ascii_frames_{job_id}_{format}.zip",
    )
