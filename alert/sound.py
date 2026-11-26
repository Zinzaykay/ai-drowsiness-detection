"""
SoundPlayer Module - AI Drowsiness Detection System.
Quản lý việc phát và dừng âm thanh cảnh báo sử dụng pygame.mixer.
Đảm bảo không chặn luồng chính của Tkinter.
"""

import threading
from pathlib import Path

import pygame


class SoundPlayer:
    """
    Lớp quản lý phát âm thanh cảnh báo.
    Sử dụng pygame.mixer để phát file MP3 trên một thread riêng,
    tránh block luồng chính của GUI (Tkinter).
    """

    def __init__(self):
        """Khởi tạo SoundPlayer và hệ thống âm thanh pygame.mixer."""
        self._initialized = False
        self._lock = threading.Lock()
        self._init_mixer()

    def _init_mixer(self):
        """
        Khởi tạo pygame.mixer một lần duy nhất.
        Nếu mixer đã được khởi tạo trước đó thì bỏ qua.
        """
        if self._initialized:
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            self._initialized = True
        except pygame.error as e:
            print(f"[SoundPlayer] Lỗi khởi tạo pygame.mixer: {e}")
            self._initialized = False

    def play(self, sound_path: str | Path) -> bool:
        """
        Phát file âm thanh được chỉ định.
        Dừng âm thanh hiện tại (nếu có) trước khi phát file mới.

        :param sound_path: Đường dẫn tới file âm thanh (hỗ trợ MP3, WAV).
        :return: True nếu phát thành công, False nếu thất bại.
        """
        sound_path = Path(sound_path)

        if not sound_path.exists():
            print(f"[SoundPlayer] File âm thanh không tồn tại: {sound_path}")
            return False

        if not self._initialized:
            self._init_mixer()
            if not self._initialized:
                print("[SoundPlayer] Không thể phát âm thanh: mixer chưa khởi tạo.")
                return False

        with self._lock:
            try:
                # Dừng nhạc hiện tại trước khi phát file mới
                pygame.mixer.music.stop()
                pygame.mixer.music.load(str(sound_path))
                pygame.mixer.music.play()
                return True
            except pygame.error as e:
                print(f"[SoundPlayer] Lỗi phát âm thanh '{sound_path.name}': {e}")
                return False

    def stop(self):
        """Dừng âm thanh đang phát."""
        if not self._initialized:
            return

        with self._lock:
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
            except pygame.error as e:
                print(f"[SoundPlayer] Lỗi dừng âm thanh: {e}")

    def is_playing(self) -> bool:
        """
        Kiểm tra xem có âm thanh đang được phát hay không.

        :return: True nếu đang phát, False nếu không.
        """
        if not self._initialized:
            return False

        try:
            return pygame.mixer.music.get_busy()
        except pygame.error:
            return False

    def cleanup(self):
        """
        Giải phóng tài nguyên âm thanh một cách an toàn.
        Dừng nhạc và tắt mixer.
        """
        if not self._initialized:
            return

        with self._lock:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except pygame.error as e:
                print(f"[SoundPlayer] Lỗi khi giải phóng tài nguyên: {e}")
            finally:
                self._initialized = False
