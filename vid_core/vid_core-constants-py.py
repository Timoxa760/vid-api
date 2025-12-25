"""
Константы и ASCII-наборы для конвертации
"""

# ASCII-наборы символов для разных стилей
ASCII_SETS = {
    "normal": " .:-=+*#%@",
    "inverted": "@%#*+=-:. ",
    "dots": " ∙·∘○◎●",
    "gradient": " ░▒▓█",
    "blocks": " ▁▂▃▄▅▆▇█",
    "thick": " ███░",
    "thin": " ·┉┊─",
}

# Цветовые палитры
COLOR_PALETTES = {
    "green": {
        "fg": "#00FF00",  # Ярко-зелёный
        "bg": "#000000",  # Чёрный
    },
    "amber": {
        "fg": "#FFAA00",  # Оранжево-жёлтый
        "bg": "#000000",
    },
    "blue": {
        "fg": "#00AAFF",  # Ярко-голубой
        "bg": "#000000",
    },
    "purple": {
        "fg": "#FF00FF",  # Пурпурный
        "bg": "#000000",
    },
    "white": {
        "fg": "#FFFFFF",  # Белый
        "bg": "#000000",
    },
    "monochrome": {
        "fg": "#CCCCCC",  # Светло-серый
        "bg": "#000000",
    },
}

# Размеры по умолчанию
DEFAULT_CHAR_ASPECT_RATIO = 0.5  # Соотношение высоты к ширине символа в терминале
DEFAULT_WIDTH = 120
DEFAULT_HEIGHT = 40

# Пороги яркости
BRIGHTNESS_THRESHOLD = 0.5  # Для определения прозрачных областей

# Максимальные размеры
MAX_WIDTH = 240
MIN_WIDTH = 10
MAX_HEIGHT = 120
MIN_HEIGHT = 10

# Форматы видео
SUPPORTED_VIDEO_FORMATS = [
    "mp4", "avi", "mov", "mkv", "flv", "wmv", "webm", "m4v",
    "3gp", "ts", "m2ts", "mts", "mxf"
]

# Форматы изображений
SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "bmp", "gif", "webp"]

# Максимальный размер файла (в байтах)
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

# Расширения файлов
FRAME_TXT_EXT = ".txt"
FRAME_PNG_EXT = ".png"
VIDEO_MP4_EXT = ".mp4"

# Шаблоны имён файлов
FRAME_FILENAME_TEMPLATE = "frame_{:06d}"
VIDEO_FILENAME = "ascii_video"
FRAMES_ZIP_FILENAME = "ascii_frames"

# FFmpeg параметры
FFMPEG_PRESET = "fast"  # fast, medium, slow (скорость кодирования)
DEFAULT_CRF = 23  # Quality (0-51, где 0=без потерь, 51=хуже всего)

# Логирование
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Статусы задач
JOB_STATUS_PENDING = "pending"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELLED = "cancelled"

# Таймауты
VIDEO_READ_TIMEOUT = 60  # секунды
FRAME_PROCESSING_TIMEOUT = 10  # секунды
VIDEO_ENCODING_TIMEOUT = 600  # секунды
