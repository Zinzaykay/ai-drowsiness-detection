"""
Component hiển thị trạng thái tỉnh táo và lời nhận xét/đánh giá của tài xế.
"""

import customtkinter as ctk
from app import app_config


class StatusPanel(ctk.CTkFrame):
    """
    Component hiển thị trạng thái tài xế (Driver Status):
    - Badge trạng thái lớn (Icon + ALERT/WARNING/DROWSY)
    - Dòng trạng thái tỉnh táo
    - Dòng nhận xét / lời khuyên an toàn
    """

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("corner_radius", 12)
        kwargs.setdefault("fg_color", ("gray95", "#1e293b"))
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", ("gray80", "#334155"))
        super().__init__(parent, **kwargs)

        self.current_status_type = "ALERT"
        self._build_ui()

    def _build_ui(self):
        """Khởi tạo giao diện thẻ trạng thái."""
        self.grid_columnconfigure(0, weight=1)

        # 1. Tiêu đề khung
        lbl_header = ctk.CTkLabel(
            self,
            text="⚡ TRẠNG THÁI TÀI XẾ (DRIVER STATUS)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#374151", "#e2e8f0")
        )
        lbl_header.pack(anchor="w", padx=15, pady=(12, 6))

        # 2. Badge lớn hiển thị trạng thái nổi bật
        cfg = app_config.STATUS_CONFIG["ALERT"]
        self.status_badge_frame = ctk.CTkFrame(
            self,
            corner_radius=8,
            fg_color=cfg["badge_color"],
            height=46
        )
        self.status_badge_frame.pack(fill="x", padx=15, pady=6)
        self.status_badge_frame.pack_propagate(False)

        self.lbl_status_badge = ctk.CTkLabel(
            self.status_badge_frame,
            text=f"{cfg['icon']}  {cfg['title']}",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#ffffff"
        )
        self.lbl_status_badge.pack(expand=True)

        # 3. Khung chi tiết: Trạng thái & Nhận xét
        details_box = ctk.CTkFrame(self, corner_radius=8, fg_color=("gray90", "#0f172a"))
        details_box.pack(fill="x", padx=15, pady=(6, 12))

        # Dòng 1: Trạng thái tỉnh táo
        row1 = ctk.CTkFrame(details_box, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(10, 6))

        lbl_state_title = ctk.CTkLabel(
            row1,
            text="Trạng thái:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#4b5563", "#94a3b8")
        )
        lbl_state_title.pack(side="left")

        self.lbl_state_val = ctk.CTkLabel(
            row1,
            text=cfg["status_text"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=(cfg["badge_color"], cfg["badge_color"])
        )
        self.lbl_state_val.pack(side="left", padx=(8, 0))

        # Gạch ngăn cách
        separator = ctk.CTkFrame(details_box, height=1, fg_color=("gray80", "#1e293b"))
        separator.pack(fill="x", padx=12, pady=2)

        # Dòng 2: Lời đánh giá / Nhận xét trạng thái
        row2 = ctk.CTkFrame(details_box, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(6, 10))

        lbl_advice_title = ctk.CTkLabel(
            row2,
            text="Nhận xét / Lời khuyên:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#4b5563", "#94a3b8")
        )
        lbl_advice_title.pack(anchor="w")

        self.lbl_advice_val = ctk.CTkLabel(
            row2,
            text=cfg["advice_text"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#1f2937", "#e2e8f0"),
            wraplength=380,
            justify="left"
        )
        self.lbl_advice_val.pack(anchor="w", pady=(4, 0))

    # ==========================================================================
    # CÁC PHƯƠNG THỨC PUBLIC API
    # ==========================================================================
    def update_status(self, status_type, status_text=None, advice_text=None):
        """
        Cập nhật toàn bộ khung trạng thái (ALERT / WARNING / DROWSY).
        :param status_type: "ALERT" | "WARNING" | "DROWSY"
        :param status_text: Dòng mô tả trạng thái tỉnh táo (nếu None sẽ lấy mặc định từ app_config)
        :param advice_text: Lời nhận xét / đánh giá (nếu None sẽ lấy mặc định từ app_config)
        """
        status_type = status_type.upper()
        if status_type not in app_config.STATUS_CONFIG:
            status_type = "ALERT"

        cfg = app_config.STATUS_CONFIG[status_type]
        self.current_status_type = status_type

        # 1. Cập nhật Badge
        self.status_badge_frame.configure(fg_color=cfg["badge_color"])
        self.lbl_status_badge.configure(text=f"{cfg['icon']}  {cfg['title']}")

        # 2. Cập nhật dòng trạng thái tỉnh táo
        s_text = status_text if status_text else cfg["status_text"]
        self.lbl_state_val.configure(text=s_text, text_color=cfg["badge_color"])

        # 3. Cập nhật dòng nhận xét
        a_text = advice_text if advice_text else cfg["advice_text"]
        self.lbl_advice_val.configure(text=a_text)
