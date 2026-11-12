"""
Module cửa sổ chính (GUI) của hệ thống AI Drowsiness Detection System.
Đảm nhận:
- Khởi tạo cửa sổ CustomTkinter và thiết lập Theme.
- Bố cục tổng thể (Header, Main 2 cột, Footer).
- Khởi tạo và kết nối các UI Components (CameraView, StatusPanel, MetricsPanel, HistoryPanel).
- Chuyển tiếp các sự kiện người dùng sang Controller và quản lý vòng đời đóng ứng dụng.
"""

from datetime import datetime
import customtkinter as ctk

from app import app_config
from app.components import CameraView, StatusPanel, MetricsPanel, HistoryPanel


class DrowsinessGUI(ctk.CTk):
    """
    Cửa sổ chính của ứng dụng AI Drowsiness Detection.
    Tuân thủ mô hình MVC: Chỉ xử lý hiển thị và chuyển tiếp sự kiện người dùng về Controller.
    """

    def __init__(self, controller=None):
        super().__init__()

        self.controller = controller

        # Cấu hình cửa sổ chính
        self.title(f"{app_config.APP_TITLE} - {app_config.APP_VERSION}")
        self.geometry(f"{app_config.WINDOW_WIDTH}x{app_config.WINDOW_HEIGHT}")
        self.minsize(app_config.WINDOW_MIN_WIDTH, app_config.WINDOW_MIN_HEIGHT)

        # Cấu hình Appearance Mode & Theme
        ctk.set_appearance_mode(app_config.APPEARANCE_MODE)
        ctk.set_default_color_theme(app_config.COLOR_THEME)

        # Bắt sự kiện người dùng bấm nút [X] đóng cửa sổ
        self.protocol("WM_DELETE_WINDOW", self._on_window_closing)

        # Khởi tạo giao diện
        self._build_ui()

        # Bắt đầu vòng lặp đồng hồ thời gian thực
        self._update_clock()

    def set_controller(self, controller):
        """Gán Controller cho GUI và kết nối các event handler."""
        self.controller = controller

    # ==========================================================================
    # KHỞI TẠO BỐ CỤC GIAO DIỆN CHÍNH
    # ==========================================================================
    def _build_ui(self):
        """Tạo bố cục các khu vực chính của cửa sổ."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header (Logo, Tiêu đề, Đồng hồ, Theme switch)
        self._create_header()

        # 2. Main Content (Cột trái: Camera; Cột phải: Trạng thái & Lịch sử)
        self._create_main_content()

        # 3. Footer (Thanh trạng thái chân trang)
        self._create_footer()

    def _create_header(self):
        """Tạo thanh tiêu đề phía trên cùng của ứng dụng."""
        header_frame = ctk.CTkFrame(self, corner_radius=0, height=65, fg_color=("gray90", "#111827"))
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)

        # Logo & Tên phần mềm
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        logo_icon = ctk.CTkLabel(
            title_box,
            text="👁️‍🗨️",
            font=ctk.CTkFont(size=28)
        )
        logo_icon.pack(side="left", padx=(0, 12))

        text_box = ctk.CTkFrame(title_box, fg_color="transparent")
        text_box.pack(side="left")

        app_label = ctk.CTkLabel(
            text_box,
            text="AI DROWSINESS DETECTION SYSTEM",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=("#1f2937", "#f9fafb")
        )
        app_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            text_box,
            text="Hệ Thống Giám Sát & Cảnh Báo Buồn Ngủ Tài Xế Thời Gian Thực",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#6b7280", "#94a3af")
        )
        subtitle_label.pack(anchor="w")

        # Đồng hồ số & Chuyển Theme
        controls_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_box.grid(row=0, column=2, padx=20, pady=10, sticky="e")

        self.clock_label = ctk.CTkLabel(
            controls_box,
            text="--:--:--",
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
            text_color=("#10b981", "#34d399")
        )
        self.clock_label.pack(side="left", padx=15)

        self.theme_switch = ctk.CTkSwitch(
            controls_box,
            text="Dark Mode",
            command=self._toggle_theme,
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        if app_config.APPEARANCE_MODE == "dark":
            self.theme_switch.select()
        self.theme_switch.pack(side="left")

    def _create_main_content(self):
        """Tạo khu vực dashboard 2 cột chứa các components."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)

        # Cột trái (Camera) tỉ trọng 6, Cột phải (Status + History) tỉ trọng 4
        main_frame.grid_columnconfigure(0, weight=6)
        main_frame.grid_columnconfigure(1, weight=4)
        main_frame.grid_rowconfigure(0, weight=1)

        # ----------------------------------------------------------------------
        # CỘT TRÁI: CAMERA VIEW
        # ----------------------------------------------------------------------
        left_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        left_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        left_container.grid_rowconfigure(0, weight=1)
        left_container.grid_columnconfigure(0, weight=1)

        self.camera_view = CameraView(
            left_container,
            on_toggle_camera=self._on_toggle_camera,
            on_test_status=self._on_test_status
        )
        self.camera_view.grid(row=0, column=0, sticky="nsew")

        # ----------------------------------------------------------------------
        # CỘT PHẢI: STATUS, METRICS VÀ HISTORY
        # ----------------------------------------------------------------------
        right_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_container.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        right_container.grid_rowconfigure(0, weight=4)  # Khối trạng thái & chỉ số
        right_container.grid_rowconfigure(1, weight=6)  # Khối lịch sử cảnh báo
        right_container.grid_columnconfigure(0, weight=1)

        # Thẻ bao bọc Trạng thái và Chỉ số (Status + Metrics Card)
        status_wrapper = ctk.CTkFrame(
            right_container,
            corner_radius=12,
            fg_color=("gray95", "#1e293b"),
            border_width=1,
            border_color=("gray80", "#334155")
        )
        status_wrapper.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        status_wrapper.grid_columnconfigure(0, weight=1)

        # Nhúng StatusPanel
        self.status_panel = StatusPanel(status_wrapper, fg_color="transparent", border_width=0)
        self.status_panel.pack(fill="x", padx=0, pady=0)

        # Nhúng MetricsPanel ngay dưới thông tin nhận xét của StatusPanel
        self.metrics_panel = MetricsPanel(status_wrapper)
        self.metrics_panel.pack(fill="x", padx=15, pady=(0, 12))

        # Nhúng HistoryPanel
        self.history_panel = HistoryPanel(
            right_container,
            on_clear_history=self._on_clear_history
        )
        self.history_panel.grid(row=1, column=0, sticky="nsew", pady=(0, 0))

        # Thêm 2 bản ghi log ban đầu tượng trưng
        self.history_panel.add_log("ALERT", "Hệ thống AI đã khởi tạo thành công. Sẵn sàng giám sát.")
        self.history_panel.add_log("WARNING", "Phát hiện chớp mắt dài hơn bình thường (EAR = 0.23).")

    def _create_footer(self):
        """Tạo thanh thông báo trạng thái dưới cùng."""
        footer_frame = ctk.CTkFrame(self, corner_radius=0, height=28, fg_color=("gray90", "#0f172a"))
        footer_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)

        self.lbl_footer_status = ctk.CTkLabel(
            footer_frame,
            text="● Trạng thái hệ thống: Sẵn sàng | Đang kết nối Controller",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#6b7280", "#94a3b8")
        )
        self.lbl_footer_status.pack(side="left", padx=15)

        lbl_copyright = ctk.CTkLabel(
            footer_frame,
            text="Bài Tập Lớn Trí Tuệ Nhân Tạo © 2026",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#9ca3af", "#64748b")
        )
        lbl_copyright.pack(side="right", padx=15)

    # ==========================================================================
    # CÁC PHƯƠNG THỨC TIỆN ÍCH CHO CONTROLLER GỌI (FORWARDING API)
    # ==========================================================================
    def update_camera_frame(self, cv_image):
        """Cập nhật frame hình ảnh lên CameraView."""
        self.camera_view.update_frame(cv_image)

    def set_camera_state(self, is_running: bool):
        """Cập nhật trạng thái hiển thị của nút và viewport camera."""
        self.camera_view.set_camera_state(is_running)

    def update_status(self, status_type, status_text=None, advice_text=None):
        """Cập nhật thông tin thẻ trạng thái."""
        self.status_panel.update_status(status_type, status_text, advice_text)

    def update_metrics(self, ear=None, mar=None, ear_color=None, mar_color=None):
        """Cập nhật chỉ số EAR và MAR."""
        self.metrics_panel.update_metrics(ear=ear, mar=mar, ear_color=ear_color, mar_color=mar_color)

    def add_alert_log(self, level, message, timestamp=None):
        """Thêm một dòng nhật ký vào lịch sử cảnh báo."""
        self.history_panel.add_log(level, message, timestamp)

    def clear_alert_history(self):
        """Xóa toàn bộ các dòng nhật ký trong lịch sử cảnh báo."""
        self.history_panel.clear_logs()

    def set_footer_status(self, text: str):
        """Cập nhật dòng thông báo trạng thái dưới footer."""
        self.lbl_footer_status.configure(text=text)

    # ==========================================================================
    # CÁC TIỆN ÍCH NỘI BỘ VÀ EVENT HANDLERS
    # ==========================================================================
    def _update_clock(self):
        """Cập nhật đồng hồ số thời gian thực mỗi giây."""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.configure(text=current_time)
        self.after(1000, self._update_clock)

    def _toggle_theme(self):
        """Chuyển đổi giữa chế độ Dark và Light."""
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def _on_toggle_camera(self):
        """Chuyển tiếp sự kiện nhấn nút Bật/Tắt Camera tới Controller."""
        if self.controller:
            self.controller.toggle_camera()

    def _on_test_status(self, level):
        """Chuyển tiếp sự kiện nhấn nút Test nhanh trạng thái tới Controller."""
        if self.controller:
            self.controller.test_change_status(level)

    def _on_clear_history(self):
        """Chuyển tiếp sự kiện nhấn nút Xóa lịch sử tới Controller."""
        if self.controller:
            self.controller.clear_history()

    def _on_window_closing(self):
        """
        Xử lý khi người dùng nhấn nút đóng cửa sổ (WM_DELETE_WINDOW).
        Ủy thác cho Controller giải phóng tài nguyên trước khi đóng.
        """
        if self.controller and hasattr(self.controller, "on_closing"):
            self.controller.on_closing()
        else:
            self.destroy()
