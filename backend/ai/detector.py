from pathlib import Path
from time import monotonic

import cv2
import mediapipe as mp
from ultralytics import YOLO


SLEEP_WARNING_SECONDS = 1.5
FACE_MISSING_WARNING_SECONDS = 1.5

# MediaPipe Face Mesh eye landmarks
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

EYE_CLOSED_THRESHOLD = 0.20


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

    @staticmethod
    def distance(point1, point2):
        return (
            (point1.x - point2.x) ** 2
            + (point1.y - point2.y) ** 2
        ) ** 0.5

    def eye_aspect_ratio(self, landmarks, eye_indices):
        p1, p2, p3, p4, p5, p6 = [
            landmarks[index] for index in eye_indices
        ]

        vertical_1 = self.distance(p2, p6)
        vertical_2 = self.distance(p3, p5)
        horizontal = self.distance(p1, p4)

        if horizontal == 0:
            return 0.0

        return (vertical_1 + vertical_2) / (2.0 * horizontal)

    def analyze(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.face_mesh.process(rgb)

        now = monotonic()

        face_detected = bool(result.multi_face_landmarks)
        sleepy = False

        if face_detected:
            self.face_missing_since = None

            landmarks = result.multi_face_landmarks[0].landmark

            left_ear = self.eye_aspect_ratio(
                landmarks,
                LEFT_EYE,
            )

            right_ear = self.eye_aspect_ratio(
                landmarks,
                RIGHT_EYE,
            )

            average_ear = (left_ear + right_ear) / 2.0

            if average_ear < EYE_CLOSED_THRESHOLD:
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
            verbose=False,
            conf=0.25,
        )

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                class_name = self.class_names[class_id]

                if (
                    class_name == "cell phone"
                    and confidence >= 0.25
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
            "focused": (
                face_detected
                and not phone_detected
                and not sleepy
            ),
            "event": event,
            "warning": warning,
        }