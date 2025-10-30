"""
Entry point cho Ứng dụng Kiosk Chấm công
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import messagebox

from services import db
from services.face import ensure_face_lib
from ui.kiosk_window import KioskWindow

def main():
    """Hàm chạy chính cho Kiosk"""
    
    # 1. Kiểm tra thư viện Face Recognition
    try:
        ensure_face_lib()
        print("✅ Thư viện face_recognition đã sẵn sàng")
    except Exception as e:
        messagebox.showerror(
            "Lỗi nghiêm trọng", 
            f"Không tải được thư viện face_recognition:\n\n{e}\n\n"
            f"Vui lòng cài đặt:\npip install face-recognition"
        )
        return

    # 2. Kiểm tra kết nối CSDL
    try:
        db.init_db()
    except Exception as e:
        messagebox.showerror(
            "Lỗi CSDL", 
            f"Không thể kết nối CSDL:\n\n{e}\n\n"
            f"Vui lòng kiểm tra:\n"
            f"- MySQL Server đã chạy\n"
            f"- Thông tin kết nối trong config.py"
        )
        return

    # 3. Khởi chạy Kiosk
    try:
        print("🚀 Khởi động Kiosk...")
        app = KioskWindow()
        if app.winfo_exists():
            print("✅ Kiosk đã sẵn sàng")
            app.mainloop()
    except Exception as e:
        messagebox.showerror("Lỗi không xác định", f"Lỗi: {e}")

if __name__ == "__main__":
    main()