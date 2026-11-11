"""
Controller Module - AI Drowsiness Detection System.
Đóng vai trò điều phối trung tâm (MVC):
Kết nối giữa Giao diện người dùng (GUI) và các module xử lý sau này (Camera, AI Detection, Alert Sound).
"""

import time
from app import app_config


class AppController:
    """
    Lớp điều khiển trung tâm của ứng dụng.
    Quản lý trạng thái, điều phối dữ liệu giữa GUI và các module backend.
    """

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
        self.alert_cooldown = 5.0  # Thời gian giãn cách tối thiểu giữa các lần ghi log cùng cấp độ (giây)

        # Tham chiếu tới các module sẽ tích hợp ở các giai đoạn tiếp theo
        self.camera_module = None
        self.face_detector = None
        self.feature_extractor = None
        self.drowsiness_classifier = None
        self.alert_manager = None

    def set_gui(self, gui):
        """Gán đối tượng GUI cho controller."""
        self.gui = gui

    # ==========================================================================
    # QUẢN LÝ CAMERA (CAMERA CONTROLS)
    # ==========================================================================
    def toggle_camera(self):
        """
        Bật hoặc Tắt Camera khi người dùng nhấn nút trên giao diện.
        Ở giai đoạn hiện tại (GUI Refactor), hoạt động ở dạng Mock để kiểm thử giao diện.
        CameraWorker đa luồng sẽ được tích hợp ở prompt tiếp theo.
        """
        if not self.is_camera_running:
            self.start_camera()
        else:
            self.stop_camera()

    def start_camera(self):
        """Khởi động camera (Mock)."""
        self.is_camera_running = True

        if self.gui:
            self.gui.set_camera_state(True)
            self.gui.set_footer_status("● Trạng thái hệ thống: Camera đang bật (Chờ kết nối CameraWorker)")
            self.gui.add_alert_log(
                level="ALERT",
                message="Đã khởi động camera giám sát."
            )

    def stop_camera(self):
        """Dừng camera (Mock) và giải phóng trạng thái."""
        self.is_camera_running = False

        if self.gui:
            self.gui.set_camera_state(False)
            self.gui.set_footer_status("● Trạng thái hệ thống: Sẵn sàng | Camera đang tắt")
            self.gui.add_alert_log(
                level="ALERT",
                message="Đã dừng camera giám sát."
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
                advice_text=advice_text
            )
            self.gui.update_metrics(
                ear=ear,
                mar=mar,
                ear_color=ear_color,
                mar_color=mar_color
            )

            # 3. Cơ chế ghi log có kiểm soát (Tránh ghi log lặp lại mỗi frame)
            now = time.time()
            is_status_changed = (status_level != self.last_logged_status)
            is_cooldown_expired = (now - self.last_alert_time >= self.alert_cooldown)

            # Chỉ ghi log khi đổi trạng thái HOẶC khi cảnh báo nguy hiểm lặp lại sau khoảng cooldown
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
        Rõ ràng là dữ liệu kiểm thử, không can thiệp vào trạng thái camera thực.
        """
        status_level = status_level.upper()

        if status_level == "ALERT":
            self.update_driver_status(
                status_level="ALERT",
                status_text="Bình thường - Đang tập trung",
                advice_text="Tài xế đang chú ý quan sát đường đi, không có dấu hiệu mệt mỏi.",
                ear=0.33,
                mar=0.18
            )
        elif status_level == "WARNING":
            self.update_driver_status(
                status_level="WARNING",
                status_text="Có dấu hiệu mệt mỏi / Mất tập trung",
                advice_text="Phát hiện chớp mắt chậm hoặc ngáp liên tục. Vui lòng giữ tập trung!",
                ear=0.22,
                mar=0.68
            )
        elif status_level == "DROWSY":
            self.update_driver_status(
                status_level="DROWSY",
                status_text="CỰC KỲ NGUY HIỂM - ĐANG NGỦ GẬT!",
                advice_text="CẢNH BÁO NGUY CƠ TAI NẠN CAO! Dừng xe tại trạm dừng gần nhất để nghỉ ngơi!",
                ear=0.14,
                mar=0.78
            )

        if self.gui:
            self.gui.set_footer_status(f"● Chế độ Test Demo: Đã chuyển sang trạng thái {status_level}")

    def clear_history(self):
        """
        Xóa toàn bộ lịch sử cảnh báo:
        - Xóa sạch danh sách log trong HistoryPanel.
        - Không tự động chèn thêm log mới vào danh sách.
        - Thông báo thành công hiển thị ở Footer.
        """
        if self.gui:
            self.gui.clear_alert_history()
            self.gui.set_footer_status("● Lịch sử cảnh báo đã được làm sạch.")

    # ==========================================================================
    # QUẢN LÝ VÒNG ĐỜI VÀ CÁC HOOKS TÍCH HỢP CHO TƯƠNG LAI
    # ==========================================================================
    def process_frame(self, frame):
        """
        Hook xử lý một khung hình:
        Sẽ được kết nối với CameraWorker và pipeline AI ở prompt tiếp theo.
        """
        pass

    def on_closing(self):
        """
        Xử lý dọn dẹp khi người dùng đóng ứng dụng:
        Đảm bảo Controller dừng camera và giải phóng tài nguyên trước khi hủy GUI.
        """
        if self.is_camera_running:
            self.stop_camera()

        if self.gui:
            self.gui.destroy()
