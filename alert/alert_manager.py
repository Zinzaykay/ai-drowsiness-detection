"""
AlertManager Module - AI Drowsiness Detection System.
Quản lý logic cảnh báo: ánh xạ trạng thái tài xế tới file âm thanh phù hợp,
xử lý ưu tiên mức độ nghiêm trọng, và cơ chế chống phát lặp (cooldown).
"""

import time
from pathlib import Path
from typing import Optional

from app import app_config
from alert.sound import SoundPlayer


# Thứ tự ưu tiên mức độ nghiêm trọng (số càng cao càng nguy hiểm)
_SEVERITY_ORDER = {
    "ALERT": 0,
    "WARNING": 1,
    "DROWSY": 2,
}

# Ánh xạ trạng thái tới file âm thanh
_STATUS_SOUND_MAP = {
    "ALERT": None,  # ALERT = tỉnh táo → không phát âm thanh
    "WARNING": app_config.WARNING_SOUND_PATH,
    "DROWSY": app_config.DROWSY_SOUND_PATH,
}


class AlertManager:
    """
    Lớp quản lý logic cảnh báo buồn ngủ.

    Chức năng chính:
    - Ánh xạ trạng thái tài xế (ALERT, WARNING, DROWSY) tới file âm thanh.
    - Phát âm thanh khi trạng thái là WARNING hoặc DROWSY.
    - Dừng âm thanh khi trạng thái chuyển về ALERT.
    - Chống phát lặp bằng cooldown cho handle_status() từ AI.
    - Ưu tiên DROWSY hơn WARNING (không hạ mức cảnh báo khi đang phát mức cao hơn).
    - Hỗ trợ test_play() cho kiểm thử GUI, bỏ qua cooldown.
    """

    # Thời gian cooldown (giây) giữa các lần phát âm thanh cùng trạng thái
    # khi nhận tín hiệu từ AI (handle_status). Không áp dụng cho test_play.
    DEFAULT_COOLDOWN = 5.0

    def __init__(self, cooldown: float = None):
        """
        Khởi tạo AlertManager.

        :param cooldown: Thời gian cooldown (giây) giữa các lần phát cùng trạng thái.
                         Mặc định DEFAULT_COOLDOWN.
        """
        self._player = SoundPlayer()
        self._cooldown = cooldown if cooldown is not None else self.DEFAULT_COOLDOWN

        # Trạng thái nội bộ
        self._current_status: str = "ALERT"
        self._last_play_time: float = 0.0
        self._last_played_status: Optional[str] = None

    # ==========================================================================
    # API CHÍNH - XỬ LÝ TRẠNG THÁI TỪ AI / CONTROLLER
    # ==========================================================================
    def handle_status(self, status: str):
        """
        Xử lý trạng thái thực tế nhận được từ AI Predictor hoặc Controller.
        Có áp dụng cooldown để tránh phát âm thanh liên tục mỗi frame.

        :param status: Trạng thái tài xế - "ALERT", "WARNING", hoặc "DROWSY".
        """
        status = status.upper()
        if status not in _SEVERITY_ORDER:
            return

        # ALERT → dừng âm thanh
        if status == "ALERT":
            self._stop_and_reset()
            return

        # Nếu đang phát âm thanh mức nghiêm trọng cao hơn → không hạ cấp
        if self._is_higher_priority_playing(status):
            return

        # Cooldown: tránh phát lặp cùng trạng thái liên tục
        now = time.time()
        if (status == self._last_played_status
                and (now - self._last_play_time) < self._cooldown):
            return

        # Phát âm thanh tương ứng
        self._play_for_status(status)

    # ==========================================================================
    # API KIỂM THỬ GUI - BỎ QUA COOLDOWN
    # ==========================================================================
    def test_play(self, status: str):
        """
        Phát âm thanh phục vụ kiểm thử GUI.
        Không bị giới hạn bởi cooldown, luôn phát lại khi nhấn nút.

        :param status: Trạng thái cần kiểm thử - "ALERT", "WARNING", hoặc "DROWSY".
        """
        status = status.upper()
        if status not in _SEVERITY_ORDER:
            return

        # ALERT → dừng âm thanh
        if status == "ALERT":
            self._stop_and_reset()
            return

        # Luôn phát lại, bỏ qua cooldown
        self._play_for_status(status)

    # ==========================================================================
    # ĐIỀU KHIỂN ÂM THANH
    # ==========================================================================
    def stop(self):
        """Dừng âm thanh hiện tại."""
        self._player.stop()

    def cleanup(self):
        """Giải phóng tài nguyên của SoundPlayer."""
        self._player.stop()
        self._player.cleanup()

    def is_playing(self) -> bool:
        """Kiểm tra xem có âm thanh đang phát hay không."""
        return self._player.is_playing()

    @property
    def current_status(self) -> str:
        """Trạng thái hiện tại mà AlertManager đang xử lý."""
        return self._current_status

    # ==========================================================================
    # CÁC PHƯƠNG THỨC NỘI BỘ
    # ==========================================================================
    def _play_for_status(self, status: str):
        """
        Phát file âm thanh tương ứng với trạng thái.

        :param status: "WARNING" hoặc "DROWSY".
        """
        sound_path = _STATUS_SOUND_MAP.get(status)
        if sound_path is None:
            return

        success = self._player.play(sound_path)
        if success:
            self._current_status = status
            self._last_played_status = status
            self._last_play_time = time.time()

    def _stop_and_reset(self):
        """Dừng âm thanh và đặt lại trạng thái về ALERT."""
        self._player.stop()
        self._current_status = "ALERT"
        self._last_played_status = None

    def _is_higher_priority_playing(self, incoming_status: str) -> bool:
        """
        Kiểm tra xem có đang phát âm thanh với mức nghiêm trọng cao hơn không.
        Ví dụ: đang phát DROWSY thì không cho WARNING ghi đè.

        :param incoming_status: Trạng thái mới muốn phát.
        :return: True nếu đang phát mức cao hơn, False nếu không.
        """
        if not self._player.is_playing():
            return False

        current_severity = _SEVERITY_ORDER.get(self._current_status, 0)
        incoming_severity = _SEVERITY_ORDER.get(incoming_status, 0)

        return incoming_severity < current_severity
