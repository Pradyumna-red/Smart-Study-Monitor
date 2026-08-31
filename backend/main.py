from pathlib import Path
from time import time

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from ai.detector import StudyDetector


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "yolov8n.pt"
AUDIO_FILES = {
    "sleep": PROJECT_ROOT / "alarm.mp3",
    "face": PROJECT_ROOT / "faudio.mp3",
    "phone": PROJECT_ROOT / "paudio.mp3",
}

app = FastAPI(title="Smart Study Monitor API")

# CORS lets the Vite app on port 5173 call this API on port 8000 in the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://smart-study-monitor-pearl.vercel.app",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# A small in-memory session is enough for one local beginner project.
session = {
    "active": False,
    "started_at": None,
    "distraction_count": 0,
    "phone_detections": 0,
    "sleep_warnings": 0,
}
detector = None


def get_detector():
    """Load the AI models only when the first frame is sent."""
    global detector
    if detector is None:
        if not MODEL_PATH.exists():
            raise HTTPException(status_code=500, detail="YOLO model file yolov8n.pt was not found.")
        try:
            detector = StudyDetector(MODEL_PATH)
        except Exception as error:
            raise HTTPException(status_code=500, detail=f"Could not load AI models: {error}") from error
    return detector


def current_status():
    study_time = 0
    if session["active"] and session["started_at"] is not None:
        study_time = int(time() - session["started_at"])
    return {
        "active": session["active"],
        "study_time": study_time,
        "distraction_count": session["distraction_count"],
        "phone_detections": session["phone_detections"],
        "sleep_warnings": session["sleep_warnings"],
    }


@app.get("/")
def home():
    return {"message": "Smart Study Monitor API is running"}


@app.get("/audio/{alarm_name}")
def get_alarm(alarm_name: str):
    """Send one existing MP3 file to the browser for browser-side playback."""
    audio_file = AUDIO_FILES.get(alarm_name)
    if audio_file is None or not audio_file.exists():
        raise HTTPException(status_code=404, detail="Alarm file was not found.")
    return FileResponse(audio_file, media_type="audio/mpeg")


@app.post("/monitor/start")
def start_monitoring():
    session.update(
        active=True,
        started_at=time(),
        distraction_count=0,
        phone_detections=0,
        sleep_warnings=0,
    )
    if detector is not None:
        detector.reset()
    return {"message": "Monitoring started", **current_status()}


@app.post("/monitor/stop")
def stop_monitoring():
    session["active"] = False
    return {"message": "Monitoring stopped", **current_status()}


@app.get("/monitor/status")
def monitor_status():
    return current_status()


@app.post("/monitor/analyze")
async def analyze_frame(frame: UploadFile = File(...)):
    if not session["active"]:
        raise HTTPException(status_code=400, detail="Start monitoring before sending frames.")
    if not frame.content_type or not frame.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image frame.")

    image_bytes = await frame.read()
    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="The uploaded image could not be read.")

    try:
        result = get_detector().analyze(image)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"AI processing error: {error}") from error

    if result["phone_detected"]:
        session["phone_detections"] += 1
    if result["sleepy"]:
        session["sleep_warnings"] += 1
    if result["phone_detected"] or result["sleepy"] or result["face_covered"]:
        session["distraction_count"] += 1

    return {**result, "metrics": current_status()}
