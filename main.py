"""
Entry point của hệ thống AI Drowsiness Detection System.
Khởi tạo giao diện người dùng (GUI) và bộ điều khiển (Controller).
"""

import sys
import os

# Đảm bảo thư mục gốc nằm trong sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.gui import DrowsinessGUI
from app.controller import AppController


def main():
    """Khởi chạy ứng dụng."""
    # 1. Khởi tạo Giao diện (GUI)
    app = DrowsinessGUI()

    # 2. Khởi tạo Controller điều phối
    controller = AppController(gui=app)

    # 3. Kết nối Controller vào GUI
    app.set_controller(controller)

    # 4. Chạy vòng lặp sự kiện chính của ứng dụng
    app.mainloop()


if __name__ == "__main__":
    main()

