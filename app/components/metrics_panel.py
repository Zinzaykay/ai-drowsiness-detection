"""
Component hiển thị các chỉ số AI theo thời gian thực (EAR, MAR).
"""

import customtkinter as ctk


class MetricsPanel(ctk.CTkFrame):
    """
    Component hiển thị các chỉ số thị giác máy tính:
    - EAR (Eye Aspect Ratio): Tỉ lệ mở mắt.
    - MAR (Mouth Aspect Ratio): Tỉ lệ mở miệng.
    
    Lưu ý kiến trúc: MetricsPanel chỉ đảm nhận hiển thị giá trị và thanh tiến trình.
    Việc xác định màu sắc (bình thường hay cảnh báo) do Controller/app_config quyết định và truyền vào,
    MetricsPanel không tự tiện so sánh ngưỡng.
    """

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(parent, **kwargs)

        self._build_ui()

    def _build_ui(self):
        """Khởi tạo giao diện 2 cột cho EAR và MAR."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Khung hiển thị EAR (Mắt)
        ear_box = ctk.CTkFrame(self, corner_radius=8, fg_color=("gray90", "#0f172a"))
        ear_box.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=0)

        ear_lbl_row = ctk.CTkFrame(ear_box, fg_color="transparent")
        ear_lbl_row.pack(fill="x", padx=8, pady=(6, 2))

        ctk.CTkLabel(
            ear_lbl_row,
            text="EAR (Mắt)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#4b5563", "#94a3b8")
        ).pack(side="left")

        self.lbl_ear_val = ctk.CTkLabel(
            ear_lbl_row,
            text="0.32",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=("#10b981", "#34d399")
        )
        self.lbl_ear_val.pack(side="right")

        self.progress_ear = ctk.CTkProgressBar(ear_box, height=6, corner_radius=3)
        self.progress_ear.pack(fill="x", padx=8, pady=(0, 8))
        self.progress_ear.set(0.64)

        # 2. Khung hiển thị MAR (Miệng)
        mar_box = ctk.CTkFrame(self, corner_radius=8, fg_color=("gray90", "#0f172a"))
        mar_box.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=0)

        mar_lbl_row = ctk.CTkFrame(mar_box, fg_color="transparent")
        mar_lbl_row.pack(fill="x", padx=8, pady=(6, 2))

        ctk.CTkLabel(
            mar_lbl_row,
            text="MAR (Miệng)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#4b5563", "#94a3b8")
        ).pack(side="left")

        self.lbl_mar_val = ctk.CTkLabel(
            mar_lbl_row,
            text="0.18",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=("#10b981", "#34d399")
        )
        self.lbl_mar_val.pack(side="right")

        self.progress_mar = ctk.CTkProgressBar(mar_box, height=6, corner_radius=3)
        self.progress_mar.pack(fill="x", padx=8, pady=(0, 8))
        self.progress_mar.set(0.25)

    # ==========================================================================
    # CÁC PHƯƠNG THỨC PUBLIC API
    # ==========================================================================
    def update_metrics(self, ear: float = None, mar: float = None, ear_color: str = None, mar_color: str = None):
        """
        Cập nhật hiển thị chỉ số EAR và MAR.
        :param ear: Giá trị số đo mắt (float).
        :param mar: Giá trị số đo miệng (float).
        :param ear_color: Mã màu cho thanh EAR (do Controller chỉ định nếu cần).
        :param mar_color: Mã màu cho thanh MAR (do Controller chỉ định nếu cần).
        """
        if ear is not None:
            self.lbl_ear_val.configure(text=f"{ear:.2f}")
            # Chuẩn hóa giá trị EAR (thường nằm trong khoảng 0.0 - 0.5)
            norm_ear = min(max(ear / 0.5, 0.0), 1.0)
            self.progress_ear.set(norm_ear)
            if ear_color:
                self.progress_ear.configure(progress_color=ear_color)
                self.lbl_ear_val.configure(text_color=ear_color)

        if mar is not None:
            self.lbl_mar_val.configure(text=f"{mar:.2f}")
            # Chuẩn hóa giá trị MAR (thường nằm trong khoảng 0.0 - 1.0)
            norm_mar = min(max(mar / 1.0, 0.0), 1.0)
            self.progress_mar.set(norm_mar)
            if mar_color:
                self.progress_mar.configure(progress_color=mar_color)
                self.lbl_mar_val.configure(text_color=mar_color)
