# Tên file: main_kiosk.py
# (Đặt ở thư mục gốc của dự án)

import tkinter as tk
from tkinter import messagebox
from services import db
from services.face import ensure_face_lib
from ui.kiosk_window import KioskWindow # <-- File này chúng ta sẽ tạo ở bước sau

def main():
    """Hàm chạy chính cho Kiosk Chấm công."""
    
    # 1. Kiểm tra thư viện Face Recognition
    try:
        ensure_face_lib()
    except Exception as e:
        messagebox.showerror(
            "Lỗi nghiêm trọng", 
            f"Không tải được thư viện face_recognition: {e}"
        )
        return

    # 2. Kiểm tra kết nối và khởi tạo CSDL
    # (Quan trọng: Phải chạy để đảm bảo bảng/admin user tồn tại)
    try:
        db.init_db()
    except Exception as e:
        messagebox.showerror(
            "Lỗi CSDL", 
            f"Không thể kết nối hoặc khởi tạo CSDL: {e}"
        )
        return

    # 3. Khởi chạy ứng dụng Kiosk
    try:
        app = KioskWindow()
        if app.winfo_exists():
            print("INFO: Khởi chạy Kiosk thành công.")
            app.mainloop()
    except Exception as e:
        messagebox.showerror("Lỗi không xác định", f"Lỗi: {e}")

if __name__ == "__main__":
    main()