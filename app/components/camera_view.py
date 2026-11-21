"""
Component hiển thị khung hình camera và các nút điều khiển liên quan.
"""

from PIL import Image, ImageDraw
import customtkinter as ctk

from app import app_config


class CameraView(ctk.CTkFrame):
    """
    Component hiển thị khung hình camera giám sát.
    Bao gồm:
    - Viewport video (hoặc placeholder khi camera tắt).
    - Nút Bật/Tắt Camera.
    - Nhóm nút kiểm thử (Demo Test).
    - Nhãn thông số kỹ thuật (Resolution, FPS).
    """

    def __init__(self, parent, on_toggle_camera=None, on_test_status=None, **kwargs):
        kwargs.setdefault("corner_radius", 12)
        kwargs.setdefault("fg_color", ("gray95", "#1e293b"))
        super().__init__(parent, **kwargs)

        self.on_toggle_camera = on_toggle_camera
        self.on_test_status = on_test_status

        self.is_camera_on = False
        self._image_reference = None

        self._build_ui()

    def set_callbacks(self, on_toggle_camera=None, on_test_status=None):
        """Thiết lập các hàm callback nhận sự kiện từ bên ngoài."""
        if on_toggle_camera:
            self.on_toggle_camera = on_toggle_camera
        if on_test_status:
            self.on_test_status = on_test_status

    def _build_ui(self):
        """Khởi tạo các thành phần giao diện của CameraView."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header của khung camera
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 6))

        title = ctk.CTkLabel(
            header,
            text="📹 KHUNG HÌNH CAMERA GIÁM SÁT",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=("#374151", "#e2e8f0")
        )
        title.pack(side="left")

        self.cam_badge_live = ctk.CTkLabel(
            header,
            text="● ĐANG TẮT",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#9ca3af", "#6b7280")
        )
        self.cam_badge_live.pack(side="right")

        # 2. Viewport hiển thị Video
        self.video_container = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=("gray85", "#0f172a"),
            border_width=1,
            border_color=("gray75", "#334155")
        )
        self.video_container.grid(row=1, column=0, sticky="nsew", padx=15, pady=6)
        self.video_container.grid_rowconfigure(0, weight=1)
        self.video_container.grid_columnconfigure(0, weight=1)

        self.video_label = ctk.CTkLabel(self.video_container, text="")
        self.video_label.grid(row=0, column=0, sticky="nsew")

        # Vẽ ảnh placeholder mặc định
        self._render_placeholder()

        # 3. Bảng điều khiển phía dưới
        controls_bar = ctk.CTkFrame(self, fg_color="transparent")
        controls_bar.grid(row=2, column=0, sticky="ew", padx=15, pady=(8, 14))
        controls_bar.grid_columnconfigure(0, weight=1)

        # Nút Bật/Tắt Camera chính
        self.btn_toggle_camera = ctk.CTkButton(
            controls_bar,
            text="▶ BẬT CAMERA",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=42,
            corner_radius=8,
            command=self._handle_toggle_camera
        )
        self.btn_toggle_camera.pack(fill="x", pady=(0, 10))

        # Khung phụ: Nút Test nhanh & Thông số
        bottom_meta = ctk.CTkFrame(controls_bar, fg_color="transparent")
        bottom_meta.pack(fill="x")

        test_group = ctk.CTkFrame(bottom_meta, fg_color="transparent")
        test_group.pack(side="left")

        test_hint = ctk.CTkLabel(
            test_group,
            text="Test nhanh:",
            font=ctk.CTkFont(size=11),
            text_color=("#6b7280", "#94a3b8")
        )
        test_hint.pack(side="left", padx=(0, 6))

        btn_test_alert = ctk.CTkButton(
            test_group,
            text="🟢 Alert",
            width=70,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            command=lambda: self._handle_test_status("ALERT")
        )
        btn_test_alert.pack(side="left", padx=2)

        btn_test_warn = ctk.CTkButton(
            test_group,
            text="⚠️ Warn",
            width=70,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#d97706",
            hover_color="#b45309",
            command=lambda: self._handle_test_status("WARNING")
        )
        btn_test_warn.pack(side="left", padx=2)

        btn_test_drowsy = ctk.CTkButton(
            test_group,
            text="🚨 Drowsy",
            width=70,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#dc2626",
            hover_color="#b91c1c",
            command=lambda: self._handle_test_status("DROWSY")
        )
        btn_test_drowsy.pack(side="left", padx=2)

        # Thông số kỹ thuật
        self.lbl_cam_meta = ctk.CTkLabel(
            bottom_meta,
            text=f"Res: {app_config.CAMERA_WIDTH}x{app_config.CAMERA_HEIGHT} | FPS: --",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=("#6b7280", "#94a3b8")
        )
        self.lbl_cam_meta.pack(side="right")
        self.video_container.grid_propagate(False)

    # ==========================================================================
    # CÁC PHƯƠNG THỨC PUBLIC API CHO GUI / CONTROLLER
    # ==========================================================================
    def set_camera_state(self, is_running: bool):
        """Cập nhật giao diện khi camera bật hoặc tắt."""
        self.is_camera_on = is_running

        if is_running:
            self.btn_toggle_camera.configure(
                text="⏹ TẮT CAMERA",
                fg_color="#ef4444",
                hover_color="#dc2626"
            )
            self.cam_badge_live.configure(
                text="● ĐANG HOẠT ĐỘNG",
                text_color="#10b981"
            )
        else:
            self.btn_toggle_camera.configure(
                text="▶ BẬT CAMERA",
                fg_color="#10b981",
                hover_color="#059669"
            )
            self.cam_badge_live.configure(
                text="● ĐANG TẮT",
                text_color=("#9ca3af", "#6b7280")
            )
            self.lbl_cam_meta.configure(
                text=f"Res: {app_config.CAMERA_WIDTH}x{app_config.CAMERA_HEIGHT} | FPS: --"
            )
            self._render_placeholder()

    def update_frame(self, cv_image):
        """
        Cập nhật một khung hình camera lên giao diện.
        :param cv_image: PIL.Image hoặc numpy BGR array.
        """
        if not self.is_camera_on:
            return

        try:
            import cv2

            container_w = self.video_container.winfo_width() - 8
            container_h = self.video_container.winfo_height() - 8

            if container_w > 50 and container_h > 50:
                orig_h, orig_w = cv_image.shape[:2]
                scale = min(container_w / orig_w, container_h / orig_h)
                new_w = max(1, int(orig_w * scale))
                new_h = max(1, int(orig_h * scale))

                # Resize bằng OpenCV siêu nhanh
                resized_bgr = cv2.resize(cv_image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                rgb_image = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_image)
            else:
                rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_image)

            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(pil_image.width, pil_image.height))
            self._image_reference = ctk_image
            self.video_label.configure(image=ctk_image, text="")
        except Exception as e:
            print(f"[CameraView Error] update_frame: {e}")

    def set_fps(self, fps: float):
        """Cập nhật giá trị FPS hiển thị."""
        self.lbl_cam_meta.configure(
            text=f"Res: {app_config.CAMERA_WIDTH}x{app_config.CAMERA_HEIGHT} | FPS: {fps:.1f}"
        )

    # ==========================================================================
    # CÁC TIỆN ÍCH NỘI BỘ VÀ XỬ LÝ SỰ KIỆN
    # ==========================================================================
    def _render_placeholder(self):
        """Vẽ hình placeholder khi camera đang tắt."""
        w, h = 640, 480
        img = Image.new("RGB", (w, h), color="#0f172a")
        draw = ImageDraw.Draw(img)

        draw.rectangle([10, 10, w - 10, h - 10], outline="#1e293b", width=2)

        cx, cy = w // 2, h // 2 - 30
        cam_w, cam_h = 100, 65

        draw.rounded_rectangle(
            [cx - cam_w // 2, cy - cam_h // 2, cx + cam_w // 2, cy + cam_h // 2],
            radius=12,
            fill="#1e293b",
            outline="#334155",
            width=2
        )
        draw.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill="#334155", outline="#475569", width=3)
        draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill="#64748b")
        draw.line([cx - 55, cy + 35, cx + 55, cy - 35], fill="#ef4444", width=4)

        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
        self._image_reference = ctk_img
        self.video_label.configure(
            image=ctk_img,
            text="Camera đang tắt\nNhấn 'BẬT CAMERA' để bắt đầu giám sát",
            compound="center",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#94a3b8"
        )

    def _handle_toggle_camera(self):
        if self.on_toggle_camera:
            self.on_toggle_camera()
        else:
            self.set_camera_state(not self.is_camera_on)

    def _handle_test_status(self, level):
        if self.on_test_status:
            self.on_test_status(level)
