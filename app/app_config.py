"""
Configuration file for AI Drowsiness Detection System.
Chứa các thiết lập về camera, ngưỡng phát hiện (thresholds), đường dẫn model, và cấu hình giao diện.
"""

from pathlib import Path

# ==============================================================================
# 1. THIẾT LẬP DỰ ÁN VÀ ĐƯỜNG DẪN (PATHS)
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# Thư mục dữ liệu & models
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
ASSETS_DIR = BASE_DIR / "assets"
ICON_DIR = ASSETS_DIR / "icon"
SOUND_DIR = ASSETS_DIR / "sound"

# Đường dẫn file model & âm thanh cảnh báo
DROWSINESS_MODEL_PATH = MODELS_DIR / "drowsiness_detector.pkl"
SHAPE_PREDICTOR_PATH = MODELS_DIR / "shape_predictor_68_face_landmarks.dat"
ALERT_SOUND_PATH = SOUND_DIR / "alarm.wav"

# ==============================================================================
# 2. CẤU HÌNH CAMERA (CAMERA SETTINGS)
# ==============================================================================
CAMERA_INDEX = 0          # 0: Webcam mặc định máy tính, 1/2: Camera ngoài hoặc USB
CAMERA_WIDTH = 640        # Chiều rộng khung hình camera
CAMERA_HEIGHT = 480       # Chiều cao khung hình camera
CAMERA_FPS = 30           # Tốc độ khung hình mong muốn

# ==============================================================================
# 3. CÁC NGƯỠNG PHÁT HIỆN AI (DETECTION THRESHOLDS)
# ==============================================================================
# Eye Aspect Ratio (EAR) - Ngưỡng phát hiện nhắm mắt
EAR_THRESHOLD = 0.25      # Nếu EAR < 0.25: mắt đang nhắm
EAR_CONSECUTIVE_FRAMES = 20  # Số frame nhắm mắt liên tiếp để kích hoạt cảnh báo (~0.7s - 1.0s)

# Mouth Aspect Ratio (MAR) - Ngưỡng phát hiện ngáp
MAR_THRESHOLD = 0.65      # Nếu MAR > 0.65: đang ngáp
MAR_CONSECUTIVE_FRAMES = 15  # Số frame mở miệng liên tiếp để tính là ngáp

# Head Pose Estimation - Ngưỡng gật đầu hoặc quay mặt
HEAD_PITCH_THRESHOLD = 20.0   # Góc gật đầu (cúi xuống ngủ)
HEAD_YAW_THRESHOLD = 25.0     # Góc quay mặt sang hai bên (mất tập trung)

# ==============================================================================
# 4. CẤU HÌNH GIAO DIỆN (UI CONFIGURATION)
# ==============================================================================
APP_TITLE = "AI Driver Drowsiness Detection System"
APP_SUBTITLE = "Hệ Thống Giám Sát & Cảnh Báo Buồn Ngủ Tài Xế"
APP_VERSION = "v1.0.0"

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_MIN_WIDTH = 1024
WINDOW_MIN_HEIGHT = 600

# Giao diện CustomTkinter
APPEARANCE_MODE = "dark"   # "dark" hoặc "light"
COLOR_THEME = "blue"       # "blue", "dark-blue", "green"

# ==============================================================================
# 5. ĐỊNH NGHĨA TRẠNG THÁI VÀ MÀU SẮC (STATUS & COLOR DEFINITIONS)
# ==============================================================================
# Bảng màu trạng thái hiện đại
STATUS_CONFIG = {
    "ALERT": {
        "title": "TỈNH TÁO (ALERT)",
        "badge_color": "#10b981",       # Emerald green
        "badge_hover": "#059669",
        "bg_color": "#064e3b",          # Dark green tint
        "border_color": "#34d399",
        "status_text": "Bình thường - Đang tập trung",
        "advice_text": "Tài xế đang chú ý quan sát đường đi, không có dấu hiệu mệt mỏi.",
        "icon": "🟢"
    },
    "WARNING": {
        "title": "CẢNH BÁO (WARNING)",
        "badge_color": "#f59e0b",       # Amber / Orange
        "badge_hover": "#d97706",
        "bg_color": "#78350f",          # Dark amber tint
        "border_color": "#fbbf24",
        "status_text": "Có dấu hiệu mệt mỏi / Mất tập trung",
        "advice_text": "Phát hiện chớp mắt chậm hoặc ngáp liên tục. Vui lòng giữ tập trung!",
        "icon": "⚠️"
    },
    "DROWSY": {
        "title": "NGỦ GẬT (DROWSY)",
        "badge_color": "#ef4444",       # Crimson Red
        "badge_hover": "#dc2626",
        "bg_color": "#7f1d1d",          # Dark red tint
        "border_color": "#f87171",
        "status_text": "CỰC KỲ NGUY HIỂM - ĐANG NGỦ GẬT!",
        "advice_text": "CẢNH BÁO NGUY CƠ TAI NẠN CAO! Dừng xe tại trạm dừng gần nhất để nghỉ ngơi!",
        "icon": "🚨"
    }
}

