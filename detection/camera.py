import cv2 as cv 
import numpy as np 
try:
    from detection.face_detector import Face_Detector
    from detection.feature_extractor import Ear
except ImportError:
    from face_detector import Face_Detector
    from feature_extractor import Ear
import time

class Camera:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None

        self.ear = Ear()
        self.face_detector = Face_Detector()
        self.landmarker = None

        self.start_time = time.time()
        self.frame_count = 0
        self.fps = 0

    def start(self):
        self.cap = cv.VideoCapture(self.camera_id)

        if not self.cap.isOpened():
            return False

        self.landmarker = (
            self.face_detector.FaceLandmarker
            .create_from_options(self.face_detector.options)
        )

        return True

    def read_frame(self):
        ret, frame = self.cap.read()

        if not ret:
            return None

        return cv.flip(frame, 1)
    def process_frame(self, frame):

        rgb_frame = self.face_detector.convert_brg_to_rgb(frame)

        mp_image = self.face_detector.convert_to_mediapipe_image(
            rgb_frame
        )

        timestamp = int(time.time() * 1000)

        result = self.landmarker.detect_for_video(
            mp_image,
            timestamp
        )

        self.face_detector.if_detect_face(
            result,
            frame
        )

        return frame

    def get_processed_frame(self):

        frame = self.read_frame()

        if frame is None:
            return None

        frame = self.process_frame(frame)

        self.calculate_fps(frame)

        return frame

    def calculate_fps(self, frame=None):
        # Tính FPS
        self.frame_count += 1
        elapsed = time.time() - self.start_time

        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = time.time()

        if frame is not None and isinstance(frame, np.ndarray):
            cv.putText(
                frame,
                f"FPS: {self.fps:.1f}",
                (20, 80),
                cv.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2
            )

        return self.fps

    def release(self):

        if self.cap is not None:
            self.cap.release()

        if self.landmarker is not None:
            self.landmarker.close()

    def get_ear(self): 
        if self.face_detector.face_landmarks is None:
            return None
        right_ear = self.ear.calculate_ear(self.face_detector.face_landmarks, self.ear.RIGHT_EYE)
        left_ear = self.ear.calculate_ear(self.face_detector.face_landmarks, self.ear.LEFT_EYE)
        return (right_ear + left_ear) / 2










