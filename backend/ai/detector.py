from pathlib import Path
from time import monotonic

import cv2
import mediapipe as mp
from ultralytics import YOLO


LEFT_EYE_TOP = 159
LEFT_EYE_BOTTOM = 145
FACE_LEFT = 130
FACE_RIGHT = 243

SLEEP_WARNING_SECONDS = 1.5
FACE_MISSING_WARNING_SECONDS = 1.5


class StudyDetector:
    def __init__(self, model_path: Path):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.phone_detector = YOLO(str(model_path))
        self.class_names = self.phone_detector.names

        self.eyes_closed_since = None
        self.face_missing_since = None

    def reset(self):
        self.eyes_closed_since = None
        self.face_missing_since = None

    def analyze(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.face_mesh.process(rgb)

        now = monotonic()
        face_detected = bool(result.multi_face_landmarks)
        sleepy = False

        if face_detected:
            self.face_missing_since = None

            landmarks = result.multi_face_landmarks[0].landmark

            top = landmarks[LEFT_EYE_TOP]
            bottom = landmarks[LEFT_EYE_BOTTOM]

            face_left = landmarks[FACE_LEFT]
            face_right = landmarks[FACE_RIGHT]

            eye_distance = ((top.x - bottom.x) ** 2 +
                            (top.y - bottom.y) ** 2) ** 0.5

            face_distance = ((face_left.x - face_right.x) ** 2 +
                             (face_left.y - face_right.y) ** 2) ** 0.5

            eye_ratio = (
                eye_distance / face_distance * 100
                if face_distance
                else 100
            )

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

        results = self.phone_detector.predict(
            frame,
            stream=True,
            verbose=False
        )

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                if (
                    self.class_names[class_id] == "cell phone"
                    and confidence > 0.5
                ):
                    phone_detected = True
                    break

            if phone_detected:
                break

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