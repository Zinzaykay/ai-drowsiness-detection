"""
Alert Package - AI Drowsiness Detection System.
Cung cấp các module quản lý cảnh báo âm thanh.
"""

from alert.alert_manager import AlertManager
from alert.sound import SoundPlayer

__all__ = ["AlertManager", "SoundPlayer"]
