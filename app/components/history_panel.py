"""
Component hiển thị danh sách lịch sử các cảnh báo buồn ngủ và sự kiện hệ thống.
"""

from datetime import datetime
import customtkinter as ctk

from app import app_config


class HistoryPanel(ctk.CTkFrame):
    """
    Component hiển thị lịch sử cảnh báo:
    - Danh sách các thẻ log có cuộn (CTkScrollableFrame).
    - Thêm bản ghi log với cấp độ (ALERT/WARNING/DROWSY) và thời gian thực.
    - Nút Xóa lịch sử.
    """

    def __init__(self, parent, on_clear_history=None, **kwargs):
        kwargs.setdefault("corner_radius", 12)
        kwargs.setdefault("fg_color", ("gray95", "#1e293b"))
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", ("gray80", "#334155"))
        super().__init__(parent, **kwargs)

        self.on_clear_history = on_clear_history
        self._history_count = 0

        self._build_ui()

    def set_callbacks(self, on_clear_history=None):
        """Thiết lập callback khi người dùng bấm nút Xóa."""
        if on_clear_history:
            self.on_clear_history = on_clear_history

    def _build_ui(self):
        """Khởi tạo giao diện thẻ lịch sử."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header: Tiêu đề + Nút Xóa
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 6))

        title = ctk.CTkLabel(
            header,
            text="📋 LỊCH SỬ CẢNH BÁO (ALERT LOGS)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#374151", "#e2e8f0")
        )
        title.pack(side="left")

        btn_clear = ctk.CTkButton(
            header,
            text="🗑 Xóa",
            width=55,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=("gray80", "#334155"),
            hover_color=("gray70", "#475569"),
            command=self._handle_clear
        )
        btn_clear.pack(side="right")

        # 2. Khung cuộn chứa danh sách log
        self.history_scroll = ctk.CTkScrollableFrame(
            self,
            corner_radius=8,
            fg_color=("gray90", "#0f172a")
        )
        self.history_scroll.grid(row=1, column=0, sticky="nsew", padx=15, pady=(4, 12))
        self.history_scroll.grid_columnconfigure(0, weight=1)

    # ==========================================================================
    # CÁC PHƯƠNG THỨC PUBLIC API
    # ==========================================================================
    def add_log(self, level: str, message: str, timestamp: str = None):
        """
        Thêm một bản ghi vào khung Lịch sử cảnh báo.
        :param level: "ALERT" | "WARNING" | "DROWSY"
        :param message: Nội dung thông điệp
        :param timestamp: Chuỗi thời gian (hh:mm:ss). Nếu None sẽ lấy giờ hiện tại.
        """
        level = level.upper()
        cfg = app_config.STATUS_CONFIG.get(level, app_config.STATUS_CONFIG["ALERT"])

        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")

        self._history_count += 1

        # Tạo thẻ log item
        item_frame = ctk.CTkFrame(
            self.history_scroll,
            corner_radius=6,
            fg_color=("gray95", "#1e293b"),
            border_width=1,
            border_color=("gray85", "#334155")
        )
        item_frame.pack(fill="x", pady=3, padx=2)
        item_frame.grid_columnconfigure(2, weight=1)

        # Cột 1: Thời gian
        lbl_time = ctk.CTkLabel(
            item_frame,
            text=timestamp,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=("#6b7280", "#94a3b8")
        )
        lbl_time.grid(row=0, column=0, padx=(8, 6), pady=6, sticky="w")

        # Cột 2: Badge mức độ
        lbl_badge = ctk.CTkLabel(
            item_frame,
            text=f" {cfg['icon']} {level} ",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#ffffff",
            fg_color=cfg["badge_color"],
            corner_radius=4
        )
        lbl_badge.grid(row=0, column=1, padx=4, pady=6)

        # Cột 3: Nội dung cảnh báo
        lbl_msg = ctk.CTkLabel(
            item_frame,
            text=message,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#1f2937", "#f1f5f9"),
            anchor="w",
            wraplength=230,
            justify="left"
        )
        lbl_msg.grid(row=0, column=2, padx=(6, 8), pady=6, sticky="w")

    def clear_logs(self):
        """Xóa toàn bộ các mục trong khung lịch sử cảnh báo."""
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
        self._history_count = 0

    def _handle_clear(self):
        if self.on_clear_history:
            self.on_clear_history()
        else:
            self.clear_logs()
