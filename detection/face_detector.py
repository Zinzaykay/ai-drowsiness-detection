import cv2 as cv 
import numpy as np 
import mediapipe as mp
try:
    from detection.feature_extractor import Ear
except ImportError:
    from feature_extractor import Ear
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
face_landmarker_path = os.path.abspath(os.path.join(current_dir, '..', 'data', 'face_landmarker.task'))

class Face_Detector:

    def __init__(self):
    # Khoi tao Mediapipe
        self.BaseOptions = mp.tasks.BaseOptions
        self.FaceLandmarker = mp.tasks.vision.FaceLandmarker
        self.FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
        self.RunningMode = mp.tasks.vision.RunningMode

    # Cấu hình Face Landmarker
        self.options = self.FaceLandmarkerOptions(
        base_options=self.BaseOptions(
            model_asset_path=face_landmarker_path
        ),
        running_mode=self.RunningMode.VIDEO,
        num_faces=1
        )
        self.face_landmarks = None

    def convert_brg_to_rgb(self,frame):
        # Chuyển BGR sang RGB
        # Thực hiện trước khi chuyển sang mediapipe_image 
        return cv.cvtColor(
            frame, cv.COLOR_BGR2RGB
        )

    def convert_to_mediapipe_image(self,rgb_frame):
        return mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

    def if_detect_face(self,result,frame):
        # Nếu phát hiện khuôn mặt
        if result.face_landmarks:

            for face_landmarks in result.face_landmarks:

                h, w, _ = frame.shape

                for landmark in face_landmarks:

                    x = int(landmark.x * w)
                    y = int(landmark.y * h)

                    cv.circle(
                        frame,
                        (x, y),
                        1,
                        (0, 255, 0),
                        -1
                    )

                cv.putText(
                    frame,
                    "Face Detected",
                    (20, 40),
                    cv.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )
                self.face_landmarks = face_landmarks
        else:
            self.face_landmarks = None
            cv.putText(
                frame,
                "No Face Detected",
                (20, 40),
                cv.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

    