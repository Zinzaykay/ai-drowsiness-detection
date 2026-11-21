"""
CameraWorker – Background thread xử lý camera, face detection và feature extraction.

Luồng hoạt động:
    Camera.read_frame() → Camera.process_frame() → Camera.get_ear() → Queue → Controller → GUI

Worker chạy trên một thread riêng, đẩy kết quả qua queue.Queue để
Controller (Main Thread) polling bằng gui.after() mà không block Tkinter.
"""

import threading
import queue
import time
import traceback
from typing import Optional

from detection.camera import Camera


class CameraWorker:
    """
    Quản lý vòng đời camera và pipeline detection trên background thread.

    Sử dụng:
        - threading.Thread cho background processing.
        - threading.Event cho tín hiệu dừng an toàn.
        - queue.Queue (có giới hạn) để truyền kết quả về Main Thread.
    """

    # Kích thước tối đa của queue – giữ nhỏ để ưu tiên frame mới nhất
    MAX_QUEUE_SIZE = 2

    def __init__(self, camera_index: int = 0, result_queue: Optional[queue.Queue] = None):
        """
        Khởi tạo CameraWorker.

        :param camera_index: Index của camera (0 = webcam mặc định).
        :param result_queue: Queue để đẩy kết quả. Nếu None sẽ tự tạo.
        """
        self.camera_index = camera_index
        self.result_queue: queue.Queue = result_queue or queue.Queue(maxsize=self.MAX_QUEUE_SIZE)

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._camera: Optional[Camera] = None

        # Timestamp tăng đơn điệu cho MediaPipe VIDEO mode
        self._timestamp_ms: int = 0

    # ===========================================================================
    # PUBLIC API
    # ===========================================================================
    def start(self) -> None:
        """Khởi chạy worker thread. Không gọi lại nếu đã đang chạy."""
        if self.is_running():
            return

        self._stop_event.clear()
        self._timestamp_ms = 0

        self._thread = threading.Thread(
            target=self._worker_loop,
            name="CameraWorkerThread",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        """
        Gửi tín hiệu dừng và chờ thread kết thúc.

        :param timeout: Thời gian chờ tối đa (giây).
                        Thread là daemon nên sẽ tự chết khi process kết thúc.
        """
        self._stop_event.set()

        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)

        self._thread = None

    def is_running(self) -> bool:
        """Kiểm tra worker thread có đang chạy không."""
        return self._thread is not None and self._thread.is_alive()

    # ===========================================================================
    # WORKER LOOP (chạy trên background thread)
    # ===========================================================================
    def _worker_loop(self) -> None:
        """
        Vòng lặp chính của worker thread.
        Mở camera + landmarker một lần, xử lý frame liên tục cho đến khi nhận
        tín hiệu dừng, sau đó giải phóng tài nguyên.
        """
        try:
            # Khởi tạo Camera (bên trong đã tạo Face_Detector + Ear)
            self._camera = Camera(camera_id=self.camera_index)

            if not self._camera.start():
                # Camera không mở được → gửi lỗi qua queue và thoát
                self._enqueue_result({
                    "frame": None,
                    "has_face": False,
                    "landmarks": None,
                    "ear": None,
                    "error": "Không thể mở camera. Kiểm tra kết nối thiết bị.",
                })
                return

            # Vòng lặp đọc và xử lý frame
            while not self._stop_event.is_set():
                result = self._process_frame()
                if result is not None:
                    self._enqueue_result(result)

        except Exception as e:
            # Lỗi không mong đợi → thông báo qua queue
            error_msg = f"CameraWorker lỗi: {e}\n{traceback.format_exc()}"
            print(f"[CameraWorker] {error_msg}")
            self._enqueue_result({
                "frame": None,
                "has_face": False,
                "landmarks": None,
                "ear": None,
                "error": error_msg,
            })
        finally:
            self._cleanup()

    def _process_frame(self) -> Optional[dict]:
        """
        Đọc một frame từ camera, chạy face detection + tính EAR.

        :return: Dictionary kết quả hoặc None nếu không đọc được frame.
        """
        if self._camera is None:
            return None

        # 1. Đọc frame từ camera
        frame = self._camera.read_frame()
        if frame is None:
            return None

        try:
            # 2. Chạy face detection (vẽ landmarks lên frame + lưu face_landmarks)
            #    Sử dụng timestamp tăng đơn điệu để đảm bảo MediaPipe VIDEO mode hoạt động đúng
            rgb_frame = self._camera.face_detector.convert_brg_to_rgb(frame)
            mp_image = self._camera.face_detector.convert_to_mediapipe_image(rgb_frame)

            self._timestamp_ms += 33  # ~30fps, luôn tăng đơn điệu
            result = self._camera.landmarker.detect_for_video(mp_image, self._timestamp_ms)

            # Vẽ landmarks lên frame và cập nhật face_detector.face_landmarks
            self._camera.face_detector.if_detect_face(result, frame)

            # 3. Kiểm tra có khuôn mặt không
            has_face = self._camera.face_detector.face_landmarks is not None

            # 4. Tính EAR nếu có khuôn mặt
            ear_value = None
            landmarks = None
            if has_face:
                landmarks = self._camera.face_detector.face_landmarks
                ear_value = self._camera.get_ear()

            # 5. Cập nhật FPS thực tế của pipeline
            fps_value = self._camera.calculate_fps()

            return {
                "frame": frame,
                "has_face": has_face,
                "landmarks": landmarks,
                "ear": ear_value,
                "fps": fps_value,
                "error": None,
            }

        except Exception as e:
            # Lỗi xử lý frame đơn lẻ → vẫn trả frame gốc để GUI hiển thị
            print(f"[CameraWorker] Lỗi xử lý frame: {e}")
            fps_value = self._camera.calculate_fps() if self._camera else 0.0
            return {
                "frame": frame,
                "has_face": False,
                "landmarks": None,
                "ear": None,
                "fps": fps_value,
                "error": None,  # Không lan truyền lỗi frame đơn lẻ
            }

    def _enqueue_result(self, result: dict) -> None:
        """
        Đẩy kết quả vào queue, loại bỏ frame cũ nếu queue đầy.
        Ưu tiên frame mới nhất thay vì để dữ liệu cũ tích tụ.
        """
        try:
            self.result_queue.put_nowait(result)
        except queue.Full:
            # Queue đầy → bỏ frame cũ nhất, đẩy frame mới
            try:
                self.result_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.result_queue.put_nowait(result)
            except queue.Full:
                pass  # Edge case cực hiếm, bỏ qua

    def _cleanup(self) -> None:
        """Giải phóng tài nguyên camera và MediaPipe landmarker."""
        if self._camera is not None:
            try:
                self._camera.release()
            except Exception as e:
                print(f"[CameraWorker] Lỗi khi giải phóng camera: {e}")
            finally:
                self._camera = None
