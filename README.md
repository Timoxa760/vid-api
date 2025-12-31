# VID-API: ASCII Video Converter REST API

Полнофункциональный REST API для преобразования видео в ASCII-анимацию, обёрнутый из оригинального проекта **Timoxa760/vid**.

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎨 Возможности

- **Конвертация видео в ASCII** с настройкой ширины, стиля и цветов
- **Сохранение результатов**:
  - Текстовые кадры (`frame_XXXXXX.txt`)
  - PNG-изображения в оригинальном разрешении
  - MP4-видео, собранное из ASCII-кадров
- **Параметризация**:
  - Ширина ASCII-символов (10-240)
  - Выбор стиля (normal, inverted, dots и т.д.)
  - Случайные цвета, прозрачный фон
  - Коррекция яркости, контраста, гаммы
- **Асинхронная обработка** с поддержкой queue
- **Потоковая передача** ASCII-кадров через WebSocket (опционально)
- **Документация** через OpenAPI (Swagger/ReDoc)
- **Docker** для быстрого развёртывания

## 📋 Требования

- Python 3.9+
- FFmpeg (для сборки MP4)
- OpenCV, NumPy, Pillow, FastAPI и др. (см. `requirements.txt`)

## 🚀 Быстрый старт

### 1. Локальная установка

```bash
# Клонировать репозиторий
git clone https://github.com/Timoxa760/vid-api.git
cd vid-api

# Создать виртуальное окружение
python3.12 -m venv venv
source venv/bin/activate  # на Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

### 2. Запуск сервера

```bash
# Development режим с автозагрузкой
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production режим
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Сервер запустится на **http://localhost:8000**

### 3. Docker

```bash
# Собрать образ
docker build -t vid-api .

# Запустить контейнер
docker run -p 8000:8000 -v /tmp/uploads:/app/uploads vid-api
```

Или используя `docker-compose`:

```bash
docker-compose up --build
```

## 📚 API Документация

### Интерактивная документация

После запуска сервера:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Основные эндпоинты

#### 1. `POST /api/v1/convert/video`
Конвертирует загруженное видео в ASCII-анимацию.

**Параметры (Form)**:
- `file` (File, required): Видеофайл (MP4, AVI, MOV и т.д.)
- `width` (int, default=120): Ширина ASCII-кадра в символах (10-240)
- `style` (str, default="normal"): Стиль ASCII (`normal`, `inverted`, `dots`, `gradient`)
- `save_txt` (bool, default=false): Сохранять текстовые кадры
- `save_png` (bool, default=true): Сохранять PNG-кадры
- `save_mp4` (bool, default=true): Собрать MP4-видео
- `brightness` (float, default=1.0): Коррекция яркости (0.5-2.0)
- `contrast` (float, default=1.0): Коррекция контраста (0.5-2.0)
- `gamma` (float, default=1.0): Гамма-коррекция (0.5-2.0)
- `random_colors` (bool, default=false): Случайные цвета для каждого кадра
- `transparent_bg` (bool, default=false): Прозрачный фон для пиксельных кадров
- `bg_color` (str, default="#000000"): HEX-цвет фона
- `text_color` (str, default="#00FF00"): HEX-цвет текста
- `fps` (int, default=30): FPS для итогового видео
- `crf` (int, default=23): Quality (0-51, где 0=lossless, 51=worst)

**Ответ**:
```json
{
  "job_id": "abc123def456",
  "status": "completed",
  "result": {
    "mp4_path": "/api/v1/download/abc123def456/video.mp4",
    "frames_count": 150,
    "duration_seconds": 5.0,
    "artifacts": {
      "txt_files": ["/api/v1/download/abc123def456/frame_000000.txt", ...],
      "png_files": ["/api/v1/download/abc123def456/frame_000000.png", ...],
      "mp4": "/api/v1/download/abc123def456/video.mp4"
    }
  },
  "processing_time_seconds": 12.5
}
```

#### 2. `POST /api/v1/convert/batch`
Конвертирует несколько видео с одинаковыми параметрами.

**Параметры**:
- `files` (List[File]): Несколько видеофайлов
- Те же параметры конвертации, что и в `/convert/video`

**Ответ**:
```json
{
  "job_ids": ["job1", "job2", "job3"],
  "batch_id": "batch_xyz789",
  "status": "processing",
  "total": 3,
  "completed": 1
}
```

#### 3. `GET /api/v1/status/{job_id}`
Получить статус обработки задачи.

**Ответ**:
```json
{
  "job_id": "abc123def456",
  "status": "processing",
  "progress": 0.65,
  "message": "Обработано 100 из 150 кадров",
  "eta_seconds": 8.5
}
```

#### 4. `GET /api/v1/download/{job_id}/{file_type}`
Скачать результаты конвертации.

**Параметры**:
- `job_id`: ID задачи
- `file_type`: `video` (MP4), `frames` (ZIP всех кадров), `txt` (ZIP текстовых кадров), `png` (ZIP PNG-кадров)

**Пример**: `GET /api/v1/download/abc123def456/video`

#### 5. `POST /api/v1/convert/stream`
Потоковая передача ASCII-кадров через WebSocket.

**WebSocket URI**: `ws://localhost:8000/api/v1/ws/convert`

**Отправить JSON**:
```json
{
  "action": "start",
  "file_base64": "...",
  "width": 120,
  "style": "normal"
}
```

**Получить JSON** (для каждого кадра):
```json
{
  "frame_number": 42,
  "ascii_text": "▓▓▓░░░...",
  "timestamp": 1.4
}
```

#### 6. `GET /api/v1/health`
Проверка статуса сервера.

**Ответ**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "active_jobs": 2
}
```

## 📝 Примеры использования

### cURL

```bash
# Простая конвертация
curl -X POST "http://localhost:8000/api/v1/convert/video" \
  -F "file=@video.mp4" \
  -F "width=100" \
  -F "style=normal" \
  -F "save_mp4=true"

# Проверить статус
curl "http://localhost:8000/api/v1/status/abc123def456"

# Скачать видео
curl "http://localhost:8000/api/v1/download/abc123def456/video" \
  -o result.mp4
```

### Python (requests)

```python
import requests

files = {'file': open('video.mp4', 'rb')}
data = {
    'width': 120,
    'style': 'normal',
    'save_mp4': True,
    'brightness': 1.2,
    'random_colors': False
}

response = requests.post(
    'http://localhost:8000/api/v1/convert/video',
    files=files,
    data=data
)

result = response.json()
job_id = result['job_id']

# Ждать завершения
import time
while True:
    status = requests.get(f'http://localhost:8000/api/v1/status/{job_id}')
    if status.json()['status'] == 'completed':
        break
    print(f"Progress: {status.json()['progress']*100:.1f}%")
    time.sleep(1)

# Скачать результат
download = requests.get(
    f'http://localhost:8000/api/v1/download/{job_id}/video',
    stream=True
)
with open('result.mp4', 'wb') as f:
    f.write(download.content)
```

### JavaScript/Fetch

```javascript
const formData = new FormData();
formData.append('file', document.getElementById('videoInput').files[0]);
formData.append('width', 120);
formData.append('style', 'normal');
formData.append('save_mp4', true);

const response = await fetch('http://localhost:8000/api/v1/convert/video', {
  method: 'POST',
  body: formData
});

const result = await response.json();
const jobId = result.job_id;

// Ждать завершения
const checkStatus = async () => {
  const status = await fetch(`http://localhost:8000/api/v1/status/${jobId}`);
  const data = await status.json();
  
  if (data.status === 'completed') {
    // Скачать результат
    window.location.href = `http://localhost:8000/api/v1/download/${jobId}/video`;
  } else {
    console.log(`Прогресс: ${data.progress*100}%`);
    setTimeout(checkStatus, 1000);
  }
};

checkStatus();
```

## ⚙️ Конфигурация

Создайте файл `.env` на основе `.env.example`:

```env
# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4
DEBUG=False

# Paths
UPLOADS_DIR=./uploads
RESULTS_DIR=./results
MAX_FILE_SIZE=500  # MB

# Processing
MAX_CONCURRENT_JOBS=4
JOB_TIMEOUT=600  # seconds
CLEANUP_AFTER=24  # hours

# Video
DEFAULT_FPS=30
DEFAULT_CRF=23
DEFAULT_WIDTH=120

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/vid-api.log
```

Загружаемые переменные через `app/config.py`.

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────┐
│          FastAPI Server (Uvicorn)           │
├─────────────────────────────────────────────┤
│                  Routes                     │
│  • POST /convert/video                      │
│  • POST /convert/batch                      │
│  • GET /status/{job_id}                     │
│  • GET /download/{job_id}/{type}            │
│  • WS /ws/convert                           │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│         Job Queue & Task Manager            │
│  (AsyncIO-based, Redis-optional)            │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│           VID Core (vid_core/)              │
│  • converter.py (главный алгоритм)          │
│  • ascii_processor.py (обработка ASCII)     │
│  • video_processor.py (ffmpeg wrapper)      │
│  • utils.py (вспомогательные функции)       │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│    External Tools & Libraries               │
│  • OpenCV (cv2) — чтение видео              │
│  • PIL — рендеринг PNG                      │
│  • NumPy — обработка матриц яркости         │
│  • FFmpeg — сборка MP4                      │
└─────────────────────────────────────────────┘
```

## 📂 Структура проекта

```
vid-api/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI приложение
│   ├── config.py                  # Pydantic settings
│   ├── models.py                  # Pydantic модели для API
│   ├── dependencies.py            # Зависимости (DI)
│   └── routes/
│       ├── __init__.py
│       ├── convert.py             # /convert/* эндпоинты
│       ├── download.py            # /download/* эндпоинты
│       ├── status.py              # /status/* эндпоинты
│       ├── health.py              # /health эндпоинт
│       └── ws.py                  # WebSocket эндпоинты
│
├── vid_core/
│   ├── __init__.py
│   ├── converter.py               # Основной класс Converter
│   ├── ascii_processor.py         # ASCII-рендеринг
│   ├── video_processor.py         # Работа с видео & FFmpeg
│   ├── image_processor.py         # Обработка кадров
│   ├── utils.py                   # Утилиты (цвета, логирование)
│   └── constants.py               # Константы (ASCII-наборы, стили)
│
├── services/
│   ├── __init__.py
│   ├── job_manager.py             # Управление задачами
│   ├── storage.py                 # Работа с файлами
│   └── notifications.py           # Уведомления (опционально)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_api.py                # Тесты API эндпоинтов
│   └── test_converter.py          # Тесты конвертера
│
├── .github/workflows/
│   └── tests.yml                  # CI/CD (GitHub Actions)
│
├── requirements.txt               # Python зависимости
├── requirements-dev.txt           # Dev зависимости (pytest, black и т.д.)
├── Dockerfile                     # Docker образ
├── docker-compose.yml             # Docker Compose конфигурация
├── .env.example                   # Пример переменных окружения
├── .dockerignore
├── .gitignore
├── README.md                      # Этот файл
├── LICENSE                        # MIT License
└── main.py                        # Entry point для быстрого запуска
```

## 🧪 Тестирование

```bash
# Установить dev зависимости
pip install -r requirements-dev.txt

# Запустить тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=app --cov=vid_core --cov-report=html

# Только интеграционные тесты
pytest tests/ -k "integration"
```

## 📊 Мониторинг и Логирование

API логирует все операции в `logs/vid-api.log` и stdout.

```python
# Пример логирования в коде
import logging

logger = logging.getLogger(__name__)
logger.info(f"Задача {job_id} начата")
logger.error(f"Ошибка обработки: {str(e)}")
```

Доступны уровни: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## 🔒 Безопасность

- **Input Validation**: Pydantic модели валидируют все входные данные
- **File Size Limits**: Ограничение размера загружаемых файлов (по умолчанию 500MB)
- **Path Traversal Protection**: Защита от атак на файловую систему
- **Rate Limiting**: Можно включить через `slowapi`
- **CORS**: По умолчанию выключен, настраивается в `config.py`

Для production:
```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🌐 Развёртывание

### Render.com

1. Запушить на GitHub
2. Создать новый Web Service на Render
3. Подключить репозиторий
4. Установить `Start Command`: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Установить `Python Version`: 3.11

### Railway.app

```bash
# Создать railway.json
{
  "build": {
    "builder": "dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "always",
    "restartPolicyMaxRetries": 5
  }
}
```

### AWS Lambda + API Gateway

Используйте `mangum` для ASGI adapter:

```python
from mangum import Mangum
from app.main import app

handler = Mangum(app)
```

## 🤝 Контрибьютинг

1. Fork репозиторий
2. Создать feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменений (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Открыть Pull Request

## 📄 Лицензия

Распространяется под лицензией MIT. См. `LICENSE` файл.

## 👨‍💻 Авторы

- **Оригинальный проект**: [Timoxa760/vid](https://github.com/Timoxa760/vid)
- **API обёртка**: VID-API Contributors

## 📞 Поддержка

- 📧 Email: support@example.com
- 💬 GitHub Issues: [Отправить issue](https://github.com/yourusername/vid-api/issues)
- 📖 Документация: [Полная документация](https://vid-api-docs.example.com)

## 🗺️ Дорожная карта

- [ ] Добавить поддержку Redis для распределённой очереди
- [ ] Реализовать WebSocket потоковую передачу кадров
- [ ] Добавить поддержку GPU-ускорения (CUDA)
- [ ] Интегрировать Amazon S3 для хранения результатов
- [ ] Создать веб-интерфейс (React/Vue)
- [ ] Добавить аутентификацию и API ключи
- [ ] Реализовать платежи через Stripe
- [ ] Добавить поддержку предустановок и шаблонов

---

**Последнее обновление**: December 2025
**Версия API**: 1.0.0
