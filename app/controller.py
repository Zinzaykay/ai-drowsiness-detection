"""
Controller Module - AI Drowsiness Detection System.
Đóng vai trò điều phối trung tâm (MVC):
Kết nối giữa Giao diện người dùng (GUI) và các module xử lý (CameraWorker, Detection).
"""

import queue
import time
from typing import Optional

from app import app_config
from app.workers.camera_worker import CameraWorker


class AppController:
    """
    Lớp điều khiển trung tâm của ứng dụng.
    Quản lý trạng thái, điều phối dữ liệu giữa GUI và CameraWorker.
    """

    # Chu kỳ polling queue (ms) – cân bằng giữa độ mượt GUI và tải CPU
    POLL_INTERVAL_MS = 30

    def __init__(self, gui=None):
        """
        Khởi tạo Controller.
        :param gui: Thể hiện của lớp DrowsinessGUI.
        """
        self.gui = gui

        # Trạng thái camera và hệ thống
        self.is_camera_running = False
        self.current_status = "ALERT"

        # Quản lý cơ chế chống spam log (Anti-Spam & Cooldown)
        self.last_logged_status = None
        self.last_alert_time = 0.0
        self.alert_cooldown = 5.0

        # CameraWorker và queue
        self._camera_worker: Optional[CameraWorker] = None
        self._result_queue: queue.Queue = queue.Queue(maxsize=CameraWorker.MAX_QUEUE_SIZE)
        self._poll_after_id = None  # ID của callback after() đang chờ

        # Tham chiếu tới các module sẽ tích hợp ở các giai đoạn tiếp theo
        self.drowsiness_classifier = None
        self.alert_manager = None

    def set_gui(self, gui):
        """Gán đối tượng GUI cho controller."""
        self.gui = gui

    # ==========================================================================
    # QUẢN LÝ CAMERA (CAMERA CONTROLS)
    # ==========================================================================
    def toggle_camera(self):
        """Bật hoặc Tắt Camera khi người dùng nhấn nút trên giao diện."""
        if not self.is_camera_running:
            self.start_camera()
        else:
            self.stop_camera()

    def start_camera(self):
        """
        Khởi động CameraWorker trên background thread.
        1. Kiểm tra camera đã chạy chưa.
        2. Tạo CameraWorker mới với queue.
        3. Khởi chạy worker thread.
        4. Bắt đầu polling queue bằng gui.after().
        5. Cập nhật trạng thái GUI.
        """
        if self.is_camera_running:
            return

        # Tạo queue mới để tránh dữ liệu cũ từ session trước
        self._result_queue = queue.Queue(maxsize=CameraWorker.MAX_QUEUE_SIZE)

        # Tạo và khởi chạy CameraWorker
        self._camera_worker = CameraWorker(
            camera_index=app_config.CAMERA_INDEX,
            result_queue=self._result_queue,
        )
        self._camera_worker.start()

        self.is_camera_running = True

        if self.gui:
            self.gui.set_camera_state(True)
            self.gui.set_footer_status("● Trạng thái hệ thống: Camera đang hoạt động")
            self.gui.add_alert_log(
                level="ALERT",
                message="Đã khởi động camera giám sát.",
            )

        # Bắt đầu polling queue trên Main Thread
        self._poll_camera_queue()

    def stop_camera(self):
        """
        Dừng CameraWorker và giải phóng tài nguyên.
        1. Hủy polling callback.
        2. Gửi tín hiệu dừng tới CameraWorker.
        3. Cập nhật GUI về trạng thái camera tắt.
        """
        # Hủy polling trước
        self._cancel_polling()

        self.is_camera_running = False

        # Dừng worker (daemon thread, timeout ngắn để không block GUI)
        if self._camera_worker is not None:
            self._camera_worker.stop(timeout=1.0)
            self._camera_worker = None

        if self.gui:
            self.gui.set_camera_state(False)
            self.gui.set_footer_status("● Trạng thái hệ thống: Sẵn sàng | Camera đang tắt")
            self.gui.add_alert_log(
                level="ALERT",
                message="Đã dừng camera giám sát.",
            )

    # ==========================================================================
    # POLLING QUEUE (chạy trên Main Thread qua gui.after())
    # ==========================================================================
    def _poll_camera_queue(self):
        """
        Lấy kết quả mới nhất từ queue và xử lý.
        Tự đăng ký lại qua gui.after() nếu camera vẫn hoạt động.
        """
        if not self.is_camera_running or self.gui is None:
            return

        # Đọc tất cả kết quả trong queue, chỉ giữ kết quả mới nhất
        latest_result = None
        try:
            while True:
                latest_result = self._result_queue.get_nowait()
        except queue.Empty:
            pass

        # Xử lý kết quả mới nhất (nếu có)
        if latest_result is not None:
            self.process_frame(latest_result)

        # Kiểm tra worker còn sống không (phát hiện crash bất ngờ)
        if self._camera_worker is not None and not self._camera_worker.is_running():
            # Worker đã chết bất ngờ
            self.is_camera_running = False
            if self.gui:
                self.gui.set_camera_state(False)
                self.gui.set_footer_status("● Trạng thái hệ thống: Camera đã dừng đột ngột")
                self.gui.add_alert_log(
                    level="WARNING",
                    message="Camera worker đã dừng đột ngột.",
                )
            self._camera_worker = None
            return

        # Đăng ký polling tiếp nếu camera vẫn hoạt động
        if self.is_camera_running:
            self._poll_after_id = self.gui.after(self.POLL_INTERVAL_MS, self._poll_camera_queue)

    def _cancel_polling(self):
        """Hủy callback after() đang chờ nếu có."""
        if self._poll_after_id is not None and self.gui is not None:
            try:
                self.gui.after_cancel(self._poll_after_id)
            except Exception:
                pass
            self._poll_after_id = None

    # ==========================================================================
    # XỬ LÝ KẾT QUẢ TỪ CAMERA WORKER
    # ==========================================================================
    def process_frame(self, result: dict):
        """
        Nhận dictionary kết quả từ CameraWorker và cập nhật GUI.

        :param result: Dictionary chứa frame, has_face, landmarks, ear, error.
        """
        if self.gui is None:
            return

        # Kiểm tra lỗi nghiêm trọng
        error = result.get("error")
        if error is not None:
            self.gui.set_footer_status(f"● Lỗi: {error}")
            self.gui.add_alert_log(level="WARNING", message=str(error))
            # Nếu không có frame → dừng camera
            if result.get("frame") is None:
                self.stop_camera()
            return

        # Cập nhật frame camera lên GUI
        frame = result.get("frame")
        if frame is not None:
            self.gui.update_camera_frame(frame)

        # Cập nhật FPS lên GUI
        fps = result.get("fps")
        if fps is not None and hasattr(self.gui, "update_fps"):
            self.gui.update_fps(fps)

        # Cập nhật metrics
        has_face = result.get("has_face", False)
        ear = result.get("ear")

        if has_face and ear is not None:
            # Có khuôn mặt → cập nhật chỉ số EAR
            # Quyết định màu sắc dựa trên ngưỡng
            ear_color = "#ef4444" if ear < app_config.EAR_THRESHOLD else "#10b981"

            self.gui.update_metrics(
                ear=ear,
                mar=None,   # Chưa hỗ trợ MAR trong module hiện tại
                ear_color=ear_color,
                mar_color=None,
            )

            # Cập nhật status – KHÔNG tự kết luận trạng thái buồn ngủ
            # khi chưa có Predictor (Random Forest). Chỉ hiển thị
            # "Đang giám sát" với chỉ số thực tế.
            self.gui.update_status(
                status_type="ALERT",
                status_text="Đang giám sát – Phát hiện khuôn mặt",
                advice_text=f"EAR: {ear:.3f} | Hệ thống đang thu thập dữ liệu. "
                            f"Module AI Predictor sẽ phân tích trạng thái tài xế.",
            )
        else:
            # Không có khuôn mặt → thông báo
            self.gui.update_metrics(
                ear=None,
                mar=None,
                ear_color=None,
                mar_color=None,
            )
            self.gui.update_status(
                status_type="WARNING",
                status_text="Không phát hiện khuôn mặt",
                advice_text="Đảm bảo khuôn mặt nằm trong khung hình camera và đủ ánh sáng.",
            )

    # ==========================================================================
    # CẬP NHẬT TRẠNG THÁI & CHỈ SỐ AI
    # ==========================================================================
    def update_driver_status(self, status_level, status_text=None, advice_text=None, ear=None, mar=None):
        """
        Cập nhật trạng thái tài xế và chỉ số lên giao diện.
        Quyết định màu sắc chỉ số theo ngưỡng trong app_config và lọc spam log.
        """
        status_level = status_level.upper()
        if status_level not in app_config.STATUS_CONFIG:
            status_level = "ALERT"

        self.current_status = status_level

        # 1. Controller quyết định màu sắc chỉ số dựa trên ngưỡng cấu hình
        ear_color = None
        if ear is not None:
            ear_color = "#ef4444" if ear < app_config.EAR_THRESHOLD else "#10b981"

        mar_color = None
        if mar is not None:
            mar_color = "#ef4444" if mar > app_config.MAR_THRESHOLD else "#10b981"

        # 2. Cập nhật lên GUI
        if self.gui:
            self.gui.update_status(
                status_type=status_level,
                status_text=status_text,
                advice_text=advice_text,
            )
            self.gui.update_metrics(
                ear=ear,
                mar=mar,
                ear_color=ear_color,
                mar_color=mar_color,
            )

            # 3. Cơ chế ghi log có kiểm soát (Tránh ghi log lặp lại mỗi frame)
            now = time.time()
            is_status_changed = (status_level != self.last_logged_status)
            is_cooldown_expired = (now - self.last_alert_time >= self.alert_cooldown)

            if is_status_changed or (status_level in ["WARNING", "DROWSY"] and is_cooldown_expired):
                cfg = app_config.STATUS_CONFIG[status_level]
                log_msg = status_text if status_text else cfg["status_text"]
                self.gui.add_alert_log(level=status_level, message=log_msg)

                self.last_logged_status = status_level
                self.last_alert_time = now

    def test_change_status(self, status_level):
        """
        Hàm hỗ trợ kiểm thử giao diện (Demo Mode):
        Mô phỏng thay đổi giữa các trạng thái ALERT, WARNING, DROWSY kèm các chỉ số mẫu.
        """
        status_level = status_level.upper()

        if status_level == "ALERT":
            self.update_driver_status(
                status_level="ALERT",
                status_text="Bình thường - Đang tập trung",
                advice_text="Tài xế đang chú ý quan sát đường đi, không có dấu hiệu mệt mỏi.",
                ear=0.33,
                mar=0.18,
            )
        elif status_level == "WARNING":
            self.update_driver_status(
                status_level="WARNING",
                status_text="Có dấu hiệu mệt mỏi / Mất tập trung",
                advice_text="Phát hiện chớp mắt chậm hoặc ngáp liên tục. Vui lòng giữ tập trung!",
                ear=0.22,
                mar=0.68,
            )
        elif status_level == "DROWSY":
            self.update_driver_status(
                status_level="DROWSY",
                status_text="CỰC KỲ NGUY HIỂM - ĐANG NGỦ GẬT!",
                advice_text="CẢNH BÁO NGUY CƠ TAI NẠN CAO! Dừng xe tại trạm dừng gần nhất để nghỉ ngơi!",
                ear=0.14,
                mar=0.78,
            )

        if self.gui:
            self.gui.set_footer_status(f"● Chế độ Test Demo: Đã chuyển sang trạng thái {status_level}")

    def clear_history(self):
        """Xóa toàn bộ lịch sử cảnh báo."""
        if self.gui:
            self.gui.clear_alert_history()
            self.gui.set_footer_status("● Lịch sử cảnh báo đã được làm sạch.")

    # ==========================================================================
    # QUẢN LÝ VÒNG ĐỜI
    # ==========================================================================
    def on_closing(self):
        """
        Xử lý dọn dẹp khi người dùng đóng ứng dụng:
        1. Dừng camera worker và giải phóng tài nguyên.
        2. Hủy các callback after() đang chờ.
        3. Đóng GUI an toàn.
        """
        # Dừng camera (bao gồm hủy polling + giải phóng worker)
        if self.is_camera_running:
            self.stop_camera()

        # Đóng GUI
        if self.gui:
            try:
                self.gui.destroy()
            except Exception:
                pass
