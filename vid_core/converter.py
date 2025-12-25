"""
Основной класс ASCIIConverter для преобразования видео в ASCII

Сохраняет всю логику из оригинального проекта vid
"""

import logging
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import subprocess
from PIL import Image, ImageDraw, ImageFont

from vid_core.constants import (
    ASCII_SETS,
    DEFAULT_CHAR_ASPECT_RATIO,
    FRAME_FILENAME_TEMPLATE,
    VIDEO_FILENAME,
    FRAME_PNG_EXT,
    FRAME_TXT_EXT,
    VIDEO_MP4_EXT,
)
from vid_core.utils import (
    hex_to_rgb,
    ensure_dir,
    get_frame_filename,
    get_video_filename,
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
    resolution: str = "high"  # low / medium / high / 4k


class ASCIIConverter:
    """Основной класс для конвертации видео в ASCII"""

    # Целевые выходные разрешения PNG/MP4
    RESOLUTIONS = {
        "low": (640, 480),
        "medium": (1280, 720),
        "high": (1920, 1080),
        "4k": (3840, 2160),
    }

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

        # Высота в символах (как и раньше)
        self.height = int(config.width * DEFAULT_CHAR_ASPECT_RATIO)

        # Целевое пиксельное разрешение выходного кадра/видео
        if config.resolution not in self.RESOLUTIONS:
            logger.warning(f"Неизвестное разрешение {config.resolution}, используется 'high'")
            self.out_width, self.out_height = self.RESOLUTIONS["high"]
        else:
            self.out_width, self.out_height = self.RESOLUTIONS[config.resolution]

        ensure_dir(str(self.output_dir))
        logger.info(
            f"Инициализирован конвертер: width={config.width} chars, "
            f"resolution={config.resolution} ({self.out_width}x{self.out_height})"
        )

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
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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
        gray = self.apply_color_corrections(frame)

        resized = cv2.resize(gray, (self.config.width, self.height))
        normalized = resized.astype(np.float32) / 255.0

        lines = []
        for row in normalized:
            line_chars = []
            for pixel in row:
                idx = int(pixel * (len(self.ascii_set) - 1))
                line_chars.append(self.ascii_set[idx])
            lines.append("".join(line_chars))

        ascii_text = "\n".join(lines)
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
        """
        Отрендерить ASCII кадр в PNG с адаптацией размера символа под целевое разрешение.
        """
        try:
            lines = ascii_text.split("\n")
            num_lines = max(len(lines), 1)

            # Целевое пиксельное разрешение выхода
            img_width = self.out_width
            img_height = self.out_height

            # Количество столбцов/строк в символах
            target_cols = max(self.config.width, 1)
            target_rows = num_lines

            base_font_size = 40  # верхняя граница, дальше будем уменьшать

            def pick_font_size():
                # Идём от большего к меньшему, чтобы максимально заполнить кадр
                for size in range(base_font_size, 4, -1):
                    font_local = None
                    for font_name in ["DejaVuSansMono.ttf", "Courier New.ttf", "consola.ttf"]:
                        try:
                            font_local = ImageFont.truetype(font_name, size)
                            break
                        except Exception:
                            continue
                    if font_local is None:
                        font_local = ImageFont.load_default()

                    # Оценим размер одного символа
                    bbox = font_local.getbbox("X")
                    char_w = bbox[2] - bbox[0]
                    char_h = bbox[3] - bbox[1]

                    text_w = char_w * target_cols
                    text_h = char_h * target_rows

                    # Влезает ли в 90% кадра по обеим осям
                    if text_w <= img_width * 0.9 and text_h <= img_height * 0.9:
                        return font_local, char_w, char_h

                # Если ничего не подошло, fallback
                font_fallback = ImageFont.load_default()
                bbox = font_fallback.getbbox("X")
                return font_fallback, (bbox[2] - bbox[0]), (bbox[3] - bbox[1])

            font, char_w, char_h = pick_font_size()

            text_width_px = char_w * target_cols
            text_height_px = char_h * target_rows

            # Центрируем текст в кадре
            x_offset = int((img_width - text_width_px) / 2)
            y_offset = int((img_height - text_height_px) / 2)

            bg_color_rgb = tuple(self.bg_color_rgb)
            text_color_rgb = tuple(self.text_color_rgb)
            img = Image.new("RGB", (img_width, img_height), bg_color_rgb)
            draw = ImageDraw.Draw(img)

            for row_idx, line in enumerate(lines):
                padded_line = line.ljust(target_cols)
                y = y_offset + row_idx * char_h
                for col_idx, ch in enumerate(padded_line):
                    x = x_offset + col_idx * char_w
                    draw.text((x, y), ch, fill=text_color_rgb, font=font)

            # Высота должна быть чётной для h264
            if img_height % 2 != 0:
                img = img.resize((img_width, img_height + 1), Image.NEAREST)

            filename = get_frame_filename(frame_number, FRAME_PNG_EXT)
            filepath = self.output_dir / filename
            img.save(str(filepath), "PNG")
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

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Не удалось открыть видео: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        src_fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(f"Видео: {total_frames} кадров, {src_fps} FPS, {width}x{height}")

        txt_files = []
        png_files = []
        frame_number = 0

        try:
            while frame_number < total_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                ascii_text = self.frame_to_ascii(frame)

                if self.config.save_txt:
                    txt_file = self.save_frame_txt(ascii_text, frame_number)
                    txt_files.append(txt_file)

                if self.config.save_png:
                    png_file = self.render_frame_png(ascii_text, frame_number)
                    png_files.append(png_file)

                frame_number += 1

                if progress_callback:
                    progress = frame_number / max(total_frames, 1)
                    progress_callback(progress, frame_number, total_frames)
        finally:
            cap.release()

        mp4_file = None
        if self.config.save_mp4 and png_files:
            mp4_file = self.create_video_from_pngs(self.config.fps or src_fps)
            logger.info(f"MP4 файл создан: {mp4_file}")

        logger.info(f"Конвертация завершена: {frame_number} кадров обработано")

        result = {
            "frames_count": frame_number,
            "fps": self.config.fps,
            "png_files": [str(f) for f in png_files],
            "txt_files": [str(f) for f in txt_files],
            "mp4_file": str(mp4_file) if mp4_file else None,
            "png_files_count": len(png_files),
            "txt_files_count": len(txt_files),
        }

        logger.info(f"Результат конвертации: {result}")
        return result

    def create_video_from_pngs(self, fps: int) -> Optional[Path]:
        """Создать MP4 видео из PNG файлов"""
        try:
            output_file = self.output_dir / get_video_filename(VIDEO_MP4_EXT)

            input_pattern = str(self.output_dir / "frame_%06d.png")
            cmd = [
                "ffmpeg",
                "-y",
                "-framerate", str(fps),
                "-i", input_pattern,
                "-vf", "format=yuv420p",
                "-crf", str(self.config.crf),
                "-preset", "medium",
                str(output_file),
            ]

            logger.info(f"Создание видео: {output_file}")
            logger.debug(f"FFmpeg команда: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"FFmpeg ошибка: {result.stderr}")
                return None

            logger.info(f"Видео успешно создано: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Ошибка при создании видео: {str(e)}")
            return None
