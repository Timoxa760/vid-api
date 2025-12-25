"""
Основной класс ASCIIConverter для преобразования видео в ASCII
Сохраняет всю логику из оригинального проекта vid
"""

import logging
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
import subprocess
import os

from vid_core.constants import (
    ASCII_SETS, DEFAULT_CHAR_ASPECT_RATIO, FRAME_FILENAME_TEMPLATE,
    VIDEO_FILENAME, FRAME_PNG_EXT, FRAME_TXT_EXT, VIDEO_MP4_EXT
)
from vid_core.utils import (
    hex_to_rgb, hex_to_bgr, ensure_dir, get_frame_filename,
    get_video_filename, format_seconds
)

logger = logging.getLogger(__name__)


@dataclass
class ConvertConfig:
    """Конфигурация преобразования"""
    width: int = 120
    style: str = "normal"
    brightness: float = 1.0
    contrast: float = 1.0
    gamma: float = 1.0
    random_colors: bool = False
    transparent_bg: bool = False
    bg_color: str = "#000000"
    text_color: str = "#00FF00"
    fps: int = 30
    crf: int = 23
    save_txt: bool = False
    save_png: bool = True
    save_mp4: bool = True


class ASCIIConverter:
    """Основной класс для конвертации видео в ASCII"""
    
    def __init__(self, output_dir: str, config: ConvertConfig):
        """
        Инициализация конвертера
        
        Args:
            output_dir: Директория для сохранения результатов
            config: Конфигурация преобразования
        """
        self.output_dir = Path(output_dir)
        self.config = config
        self.ascii_set = ASCII_SETS.get(config.style, ASCII_SETS["normal"])
        self.bg_color_rgb = hex_to_rgb(config.bg_color)
        self.text_color_rgb = hex_to_rgb(config.text_color)
        self.height = int(config.width * DEFAULT_CHAR_ASPECT_RATIO)
        
        ensure_dir(str(self.output_dir))
        logger.info(f"Инициализирован конвертер с шириной {config.width}")
    
    def calculate_height(self, width: int) -> int:
        """Вычислить высоту на основе ширины"""
        return int(width * DEFAULT_CHAR_ASPECT_RATIO)
    
    def brightness_correction(self, img: np.ndarray) -> np.ndarray:
        """Применить коррекцию яркости"""
        if self.config.brightness == 1.0:
            return img
        return np.clip(img * self.config.brightness, 0, 255).astype(np.uint8)
    
    def contrast_correction(self, img: np.ndarray) -> np.ndarray:
        """Применить коррекцию контраста"""
        if self.config.contrast == 1.0:
            return img
        mean = img.mean()
        return np.clip((img - mean) * self.config.contrast + mean, 0, 255).astype(np.uint8)
    
    def gamma_correction(self, img: np.ndarray) -> np.ndarray:
        """Применить гамма-коррекцию"""
        if self.config.gamma == 1.0:
            return img
        inv_gamma = 1.0 / self.config.gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype(np.uint8)
        return cv2.LUT(img, table)
    
    def apply_color_corrections(self, frame: np.ndarray) -> np.ndarray:
        """Применить все коррекции цвета"""
        # Преобразовать в Grayscale для обработки яркости
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Применить коррекции в порядке: яркость -> контраст -> гамма
        gray = self.brightness_correction(gray)
        gray = self.contrast_correction(gray)
        gray = self.gamma_correction(gray)
        
        return gray
    
    def frame_to_ascii(self, frame: np.ndarray) -> str:
        """
        Преобразовать кадр видео в ASCII текст
        
        Args:
            frame: OpenCV кадр (BGR)
            
        Returns:
            ASCII текст кадра
        """
        # Применить коррекции
        gray = self.apply_color_corrections(frame)
        
        # Изменить размер изображения
        resized = cv2.resize(gray, (self.config.width, self.height))
        
        # Нормализировать значения в диапазон 0-1
        normalized = resized.astype(np.float32) / 255.0
        
        # Преобразовать в ASCII
        ascii_text = ""
        for row in normalized:
            for pixel in row:
                # Найти индекс в ASCII наборе
                idx = int(pixel * (len(self.ascii_set) - 1))
                ascii_text += self.ascii_set[idx]
            ascii_text += "\n"
        
        return ascii_text
    
    def save_frame_txt(self, ascii_text: str, frame_number: int) -> Path:
        """Сохранить ASCII кадр в текстовый файл"""
        filename = get_frame_filename(frame_number, FRAME_TXT_EXT)
        filepath = self.output_dir / filename
        
        try:
            filepath.write_text(ascii_text)
            logger.debug(f"Сохранён текстовый кадр: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Ошибка при сохранении текстового кадра: {str(e)}")
            raise
    
    def render_frame_png(self, ascii_text: str, frame_number: int) -> Path:
        """Отрендерить ASCII кадр в PNG изображение"""
        # Параметры шрифта (используем OpenCV)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.3
        font_thickness = 1
        
        # Создать чёрное изображение
        img = np.zeros((
            self.height * 15,  # Примерная высота символа
            self.config.width * 8,  # Примерная ширина символа
            3
        ), dtype=np.uint8)
        img[:] = self.bg_color_rgb[::-1]  # BGR формат для OpenCV
        
        # Нарисовать текст
        y_offset = 12
        for line in ascii_text.split('\n'):
            cv2.putText(
                img, line, (5, y_offset),
                font, font_scale,
                tuple(self.text_color_rgb[::-1]),  # BGR для OpenCV
                font_thickness
            )
            y_offset += 15
        
        # Сохранить PNG
        filename = get_frame_filename(frame_number, FRAME_PNG_EXT)
        filepath = self.output_dir / filename
        
        try:
            cv2.imwrite(str(filepath), img)
            logger.debug(f"Сохранён PNG кадр: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Ошибка при сохранении PNG кадра: {str(e)}")
            raise
    
    def convert_video(
        self,
        video_path: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Преобразовать видео в ASCII
        
        Args:
            video_path: Путь к видеофайлу
            progress_callback: Функция для отчёта о прогрессе
            
        Returns:
            Словарь с результатами конвертации
        """
        logger.info(f"Начало конвертации видео: {video_path}")
        
        # Открыть видео
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Не удалось открыть видео: {video_path}")
        
        # Получить информацию о видео
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"Видео: {total_frames} кадров, {fps} FPS, {width}x{height}")
        
        # Списки для результатов
        txt_files = []
        png_files = []
        frame_number = 0
        
        try:
            while frame_number < total_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Преобразовать в ASCII
                ascii_text = self.frame_to_ascii(frame)
                
                # Сохранить результаты
                if self.config.save_txt:
                    txt_file = self.save_frame_txt(ascii_text, frame_number)
                    txt_files.append(txt_file)
                
                if self.config.save_png:
                    png_file = self.render_frame_png(ascii_text, frame_number)
                    png_files.append(png_file)
                
                frame_number += 1
                
                # Отчёт о прогрессе
                if progress_callback:
                    progress = frame_number / total_frames
                    progress_callback(frame_number, total_frames, progress)
                
                if frame_number % 10 == 0:
                    logger.debug(f"Обработано {frame_number}/{total_frames} кадров")
        
        finally:
            cap.release()
        
        logger.info(f"Конвертация завершена: {frame_number} кадров обработано")
        
        result = {
            "frames_count": frame_number,
            "fps": fps,
            "txt_files": txt_files,
            "png_files": png_files,
            "total_frames": total_frames,
        }
        
        # Собрать MP4 видео, если требуется
        if self.config.save_mp4 and png_files:
            logger.info("Начало сборки MP4 видео...")
            mp4_path = self.build_mp4_from_frames(png_files, fps)
            result["mp4_path"] = mp4_path
            logger.info(f"MP4 видео сохранено: {mp4_path}")
        
        return result
    
    def build_mp4_from_frames(self, png_files: List[Path], fps: float) -> Path:
        """
        Собрать MP4 видео из PNG кадров с помощью FFmpeg
        
        Args:
            png_files: Список путей к PNG файлам
            fps: Частота кадров
            
        Returns:
            Путь к созданному MP4 файлу
        """
        output_path = self.output_dir / get_video_filename(VIDEO_MP4_EXT)
        
        # Создать временный файл со списком кадров для FFmpeg
        concat_file = self.output_dir / "framelist.txt"
        with open(concat_file, 'w') as f:
            for png_file in png_files:
                f.write(f"file '{png_file}'\n")
        
        try:
            # Использовать FFmpeg для сборки видео
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-crf", str(self.config.crf),
                "-y",  # Перезаписать без вопроса
                str(output_path)
            ]
            
            logger.info(f"Запуск FFmpeg команды: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg ошибка: {result.stderr}")
            
            return output_path
        
        finally:
            # Удалить временный файл
            if concat_file.exists():
                concat_file.unlink()
