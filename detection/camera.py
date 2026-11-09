import cv2 as cv 
import numpy as np 
from face_detector import Face_Detector
import time

# Tạo một đối tượng của class Face_detector để khởi tạo Mediapipe 

face_detector = Face_Detector()

start_time = time.time()
frame_count = 0
fps = 0

def flip_frame(root_frame):
    return cv.flip(root_frame, 1)

def calculate_fps(frame_count,start_time,frame,fps):
    # Tính FPS
    frame_count += 1
    elapsed = time.time() - start_time

    if elapsed >= 1:
        fps = frame_count / elapsed
        frame_count = 0
        start_time = time.time()

    cv.putText(
        frame,
        f"FPS: {fps:.1f}",
        (20, 80),
        cv.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 0, 0),
        2
    )

# Khởi tạo model
with face_detector.FaceLandmarker.create_from_options(face_detector.options) as landmarker:

    # Mở webcam
    cap = cv.VideoCapture(0)

    if not cap.isOpened():
        print("Không thể mở webcam!")
        exit()

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Không đọc được camera!")
            break

        # Lật ngược khung hình lại (giống soi gương)
        frame = flip_frame(frame)

        # Chuyển BGR sang RGB
        rgb_frame = face_detector.convert_brg_to_rgb(frame)

        # Chuyển thành MediaPipe Image
        mp_image = face_detector.convert_to_mediapipe_image(rgb_frame)

        # Timestamp tính bằng milliseconds
        timestamp = int(time.time() * 1000)

        # Nhận diện khuôn mặt
        result = landmarker.detect_for_video(
            mp_image, timestamp
        )

        face_detector.if_detect_face(result,frame)

        calculate_fps(frame_count,start_time,frame,fps)

        # Hiển thị
        cv.imshow("Face Landmarker Test", frame)

        # Nhấn ESC để thoát
        if cv.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv.destroyAllWindows()







