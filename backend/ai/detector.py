from pathlib import Path
from time import monotonic

import cv2
from cvzone.FaceMeshModule import FaceMeshDetector
from ultralytics import YOLO


# These are the same landmark points and eye-ratio threshold used by app.py.
LEFT_EYE_TOP = 159
LEFT_EYE_BOTTOM = 145
FACE_LEFT = 130
FACE_RIGHT = 243
# The browser sends a frame every two seconds, unlike app.py's ~30 FPS camera loop.
# Time-based thresholds keep warnings responsive at that lower frame rate.
SLEEP_WARNING_SECONDS = 1.5
FACE_MISSING_WARNING_SECONDS = 1.5


class StudyDetector:
    """Runs one frame through the existing face and phone detection logic."""

    def __init__(self, model_path: Path):
        # Loading once is much faster than loading YOLO for every browser frame.
        self.face_detector = FaceMeshDetector(maxFaces=1)
        self.phone_detector = YOLO(str(model_path))
        self.class_names = self.phone_detector.names
        self.eyes_closed_since = None
        self.face_missing_since = None

    def reset(self):
        """Start a fresh monitoring session without old warning timers."""
        self.eyes_closed_since = None
        self.face_missing_since = None

    def analyze(self, frame):
        """Return simple detection results for one OpenCV BGR image."""
        frame, faces = self.face_detector.findFaceMesh(frame, draw=False)
        now = monotonic()
        face_detected = bool(faces)
        sleepy = False

        if face_detected:
            self.face_missing_since = None
            face = faces[0]
            eye_distance, _ = self.face_detector.findDistance(
                face[LEFT_EYE_TOP], face[LEFT_EYE_BOTTOM]
            )
            face_distance, _ = self.face_detector.findDistance(
                face[FACE_LEFT], face[FACE_RIGHT]
            )
            eye_ratio = (eye_distance / face_distance) * 100 if face_distance else 100

            if eye_ratio < 11.0:
                if self.eyes_closed_since is None:
                    self.eyes_closed_since = now
            else:
                self.eyes_closed_since = None
            sleepy = (
                self.eyes_closed_since is not None
                and now - self.eyes_closed_since >= SLEEP_WARNING_SECONDS
            )
        else:
            self.eyes_closed_since = None
            if self.face_missing_since is None:
                self.face_missing_since = now

        face_covered = (
            self.face_missing_since is not None
            and now - self.face_missing_since >= FACE_MISSING_WARNING_SECONDS
        )
        phone_detected = False

        results = self.phone_detector.predict(frame, stream=True, verbose=False)
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                if self.class_names[class_id] == "cell phone" and confidence > 0.5:
                    phone_detected = True
                    break
            if phone_detected:
                break

        # Match app.py's alert priority, but only report it; the browser owns audio.
        if face_covered:
            event = "FACE NOT DETECTED"
            warning = "FACE NOT DETECTED"
        elif sleepy:
            event = "SLEEP WARNING"
            warning = "SLEEP WARNING"
        elif phone_detected:
            event = "PHONE DETECTED"
            warning = "PHONE DETECTED"
        elif face_detected:
            event = "FACE DETECTED"
            warning = None
        else:
            event = "FACE NOT DETECTED"
            warning = None

        return {
            "face_detected": face_detected,
            "face_covered": face_covered,
            "phone_detected": phone_detected,
            "sleepy": sleepy,
            "focused": face_detected and not phone_detected and not sleepy,
            "event": event,
            "warning": warning,
        }
