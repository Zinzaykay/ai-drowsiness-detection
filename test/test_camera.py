"""
File kiểm thử độc lập module Camera và Face Landmarker.
Chạy trực tiếp file này để kiểm tra luồng camera mà không cần khởi động GUI.
"""

import sys
from pathlib import Path

# Đảm bảo thư mục gốc nằm trong sys.path khi chạy script này
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import cv2 as cv
from detection.camera import Camera


def main():
    camera = Camera()
    if not camera.start():
        print("Không thể mở camera!")
        return

    print("Camera đã khởi động. Nhấn ESC trên cửa sổ hình ảnh để dừng.")

    try:
        while True:
            frame = camera.get_processed_frame()
            if frame is None:
                print("Không đọc được frame từ camera!")
                break

            ear = camera.get_ear()
            if ear is not None:
                cv.putText(
                    frame,
                    f"EAR: {ear:.3f}",
                    (20, 120),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )

            cv.imshow("FaceLandmarker Test", frame)
            if cv.waitKey(1) & 0xFF == 27:
                break
    finally:
        camera.release()
        cv.destroyAllWindows()
        print("Đã giải phóng camera và đóng cửa sổ.")


if __name__ == "__main__":
    main()
