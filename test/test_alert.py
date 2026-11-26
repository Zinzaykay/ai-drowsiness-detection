"""
Unit Tests cho Alert Module - AI Drowsiness Detection System.
Kiểm tra logic ánh xạ trạng thái, cooldown, ưu tiên mức độ nghiêm trọng,
và xử lý lỗi của AlertManager.

Sử dụng mock SoundPlayer để kiểm tra logic mà không cần phát âm thanh thực.
"""

import sys
import os
import time
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Đảm bảo thư mục gốc dự án trong sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app_config
from alert.alert_manager import AlertManager, _STATUS_SOUND_MAP


class MockSoundPlayer:
    """Mock SoundPlayer để kiểm tra logic AlertManager mà không phát âm thanh."""

    def __init__(self):
        self._playing = False
        self._current_file = None
        self.play_count = 0
        self.stop_count = 0
        self.cleanup_called = False

    def play(self, sound_path):
        self._playing = True
        self._current_file = str(sound_path)
        self.play_count += 1
        return True

    def stop(self):
        self._playing = False
        self._current_file = None
        self.stop_count += 1

    def is_playing(self):
        return self._playing

    def cleanup(self):
        self.stop()
        self.cleanup_called = True


class TestSoundMapping(unittest.TestCase):
    """Kiểm tra ánh xạ trạng thái tới file âm thanh."""

    def test_warning_maps_to_correct_sound(self):
        """WARNING phải ánh xạ tới file âm thanh cảnh báo."""
        sound_path = _STATUS_SOUND_MAP["WARNING"]
        self.assertIsNotNone(sound_path)
        self.assertEqual(sound_path, app_config.WARNING_SOUND_PATH)

    def test_drowsy_maps_to_correct_sound(self):
        """DROWSY phải ánh xạ tới file âm thanh báo động."""
        sound_path = _STATUS_SOUND_MAP["DROWSY"]
        self.assertIsNotNone(sound_path)
        self.assertEqual(sound_path, app_config.DROWSY_SOUND_PATH)

    def test_alert_maps_to_no_sound(self):
        """ALERT không có âm thanh (None)."""
        sound_path = _STATUS_SOUND_MAP["ALERT"]
        self.assertIsNone(sound_path)

    def test_warning_sound_file_exists(self):
        """File âm thanh WARNING phải tồn tại trên đĩa."""
        self.assertTrue(
            app_config.WARNING_SOUND_PATH.exists(),
            f"File không tồn tại: {app_config.WARNING_SOUND_PATH}"
        )

    def test_drowsy_sound_file_exists(self):
        """File âm thanh DROWSY phải tồn tại trên đĩa."""
        self.assertTrue(
            app_config.DROWSY_SOUND_PATH.exists(),
            f"File không tồn tại: {app_config.DROWSY_SOUND_PATH}"
        )


class TestAlertManagerLogic(unittest.TestCase):
    """Kiểm tra logic xử lý trạng thái của AlertManager."""

    def setUp(self):
        """Tạo AlertManager với mock SoundPlayer."""
        self.manager = AlertManager(cooldown=2.0)
        self.mock_player = MockSoundPlayer()
        self.manager._player = self.mock_player

    def test_warning_triggers_sound(self):
        """handle_status('WARNING') phải phát âm thanh."""
        self.manager.handle_status("WARNING")
        self.assertEqual(self.mock_player.play_count, 1)
        self.assertEqual(self.manager.current_status, "WARNING")

    def test_drowsy_triggers_sound(self):
        """handle_status('DROWSY') phải phát âm thanh."""
        self.manager.handle_status("DROWSY")
        self.assertEqual(self.mock_player.play_count, 1)
        self.assertEqual(self.manager.current_status, "DROWSY")

    def test_alert_stops_sound(self):
        """handle_status('ALERT') phải dừng âm thanh đang phát."""
        self.manager.handle_status("DROWSY")
        self.assertTrue(self.mock_player.is_playing())

        self.manager.handle_status("ALERT")
        self.assertFalse(self.mock_player.is_playing())
        self.assertEqual(self.manager.current_status, "ALERT")

    def test_cooldown_prevents_repeated_play(self):
        """Cùng trạng thái liên tục không phát lặp lại trong thời gian cooldown."""
        self.manager.handle_status("WARNING")
        self.assertEqual(self.mock_player.play_count, 1)

        # Gọi lại ngay → bị cooldown chặn
        self.manager.handle_status("WARNING")
        self.assertEqual(self.mock_player.play_count, 1)

        # Gọi lại ngay lần nữa → vẫn bị chặn
        self.manager.handle_status("WARNING")
        self.assertEqual(self.mock_player.play_count, 1)

    def test_cooldown_expires(self):
        """Sau khi cooldown hết hạn, cùng trạng thái có thể phát lại."""
        self.manager._cooldown = 0.1  # Cooldown rất ngắn cho test

        self.manager.handle_status("WARNING")
        self.assertEqual(self.mock_player.play_count, 1)

        # Đợi cooldown hết
        time.sleep(0.15)

        self.manager.handle_status("WARNING")
        self.assertEqual(self.mock_player.play_count, 2)

    def test_drowsy_has_priority_over_warning(self):
        """DROWSY đang phát thì WARNING không được ghi đè."""
        self.manager.handle_status("DROWSY")
        self.assertEqual(self.mock_player.play_count, 1)
        self.assertEqual(self.manager.current_status, "DROWSY")

        # WARNING không được ghi đè DROWSY
        self.manager.handle_status("WARNING")
        self.assertEqual(self.mock_player.play_count, 1)  # Không phát thêm
        self.assertEqual(self.manager.current_status, "DROWSY")  # Vẫn là DROWSY

    def test_warning_can_be_upgraded_to_drowsy(self):
        """WARNING đang phát thì DROWSY có thể ghi đè (nâng cấp)."""
        self.manager.handle_status("WARNING")
        self.assertEqual(self.mock_player.play_count, 1)
        self.assertEqual(self.manager.current_status, "WARNING")

        # DROWSY ghi đè WARNING
        self.manager.handle_status("DROWSY")
        self.assertEqual(self.mock_player.play_count, 2)
        self.assertEqual(self.manager.current_status, "DROWSY")

    def test_different_status_resets_cooldown(self):
        """Chuyển sang trạng thái khác phải reset cooldown."""
        self.manager.handle_status("WARNING")
        self.assertEqual(self.mock_player.play_count, 1)

        # Chuyển sang ALERT (dừng)
        self.manager.handle_status("ALERT")
        self.assertFalse(self.mock_player.is_playing())

        # Phát lại WARNING ngay → được phép vì đã reset
        self.manager.handle_status("WARNING")
        self.assertEqual(self.mock_player.play_count, 2)

    def test_invalid_status_ignored(self):
        """Trạng thái không hợp lệ bị bỏ qua."""
        self.manager.handle_status("INVALID")
        self.assertEqual(self.mock_player.play_count, 0)
        self.assertEqual(self.manager.current_status, "ALERT")

    def test_case_insensitive_status(self):
        """Trạng thái không phân biệt hoa thường."""
        self.manager.handle_status("warning")
        self.assertEqual(self.mock_player.play_count, 1)

        self.manager.handle_status("alert")
        self.assertFalse(self.mock_player.is_playing())


class TestAlertManagerTestPlay(unittest.TestCase):
    """Kiểm tra phương thức test_play() (kiểm thử GUI, bỏ qua cooldown)."""

    def setUp(self):
        self.manager = AlertManager(cooldown=10.0)  # Cooldown dài
        self.mock_player = MockSoundPlayer()
        self.manager._player = self.mock_player

    def test_test_play_bypasses_cooldown(self):
        """test_play() luôn phát lại, không bị cooldown chặn."""
        self.manager.test_play("WARNING")
        self.assertEqual(self.mock_player.play_count, 1)

        self.manager.test_play("WARNING")
        self.assertEqual(self.mock_player.play_count, 2)

        self.manager.test_play("WARNING")
        self.assertEqual(self.mock_player.play_count, 3)

    def test_test_play_alert_stops_sound(self):
        """test_play('ALERT') dừng âm thanh đang phát."""
        self.manager.test_play("DROWSY")
        self.assertTrue(self.mock_player.is_playing())

        self.manager.test_play("ALERT")
        self.assertFalse(self.mock_player.is_playing())

    def test_test_play_switch_drowsy_to_warning(self):
        """test_play() cho phép chuyển từ DROWSY sang WARNING (GUI test)."""
        self.manager.test_play("DROWSY")
        self.assertEqual(self.manager.current_status, "DROWSY")

        # Trong test mode, luôn phát lại bất kể mức độ
        self.manager.test_play("WARNING")
        self.assertEqual(self.mock_player.play_count, 2)
        self.assertEqual(self.manager.current_status, "WARNING")


class TestAlertManagerSafety(unittest.TestCase):
    """Kiểm tra xử lý an toàn khi file không tồn tại hoặc lỗi."""

    def setUp(self):
        self.manager = AlertManager()

    def test_missing_sound_file_no_crash(self):
        """Không crash khi file âm thanh không tồn tại."""
        # Tạo mock player trả về False khi play
        mock_player = MockSoundPlayer()
        mock_player.play = MagicMock(return_value=False)
        self.manager._player = mock_player

        # Phải không raise exception
        try:
            self.manager.handle_status("WARNING")
            self.manager.test_play("DROWSY")
        except Exception as e:
            self.fail(f"Không được raise exception khi file không tồn tại: {e}")

    def test_cleanup_releases_resources(self):
        """cleanup() phải dừng và giải phóng tài nguyên."""
        mock_player = MockSoundPlayer()
        self.manager._player = mock_player

        self.manager.test_play("WARNING")
        self.manager.cleanup()

        self.assertTrue(mock_player.cleanup_called)
        self.assertFalse(mock_player.is_playing())


if __name__ == "__main__":
    unittest.main()
