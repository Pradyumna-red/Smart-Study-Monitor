FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    libgles2 \
    libgl1 \
    libxcb1 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY yolov8n.pt ./yolov8n.pt
COPY alarm.mp3 ./alarm.mp3
COPY faudio.mp3 ./faudio.mp3
COPY paudio.mp3 ./paudio.mp3

WORKDIR /app/backend

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]