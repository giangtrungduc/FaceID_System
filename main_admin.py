"""
Entry point cho Ứng dụng Quản lý (Admin)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import messagebox

from services import db
from services.face import ensure_face_lib
from ui.login_window import LoginWindow
from ui.admin_window import AdminWindow

class AdminAppController:
    """
    Controller quản lý luồng:
    1. Mở LoginWindow
    2. Nếu thành công -> Mở AdminWindow
    """
    def __init__(self, root):
        self.root = root
        self.admin_window = None
        
        # ===== THAY ĐỔI: KHÔNG withdraw root =====
        # Thay vào đó, ẩn root sau khi tạo LoginWindow
        self.root.geometry("1x1+0+0")  # Thu nhỏ root xuống 1 pixel
        self.root.overrideredirect(True)  # Ẩn thanh title bar
        
        # Delay việc mở LoginWindow
        self.root.after(100, self._show_login)

    def _show_login(self):
        """Hiển thị cửa sổ đăng nhập"""
        print("DEBUG: Đang tạo LoginWindow...")
        try:
            login_win = LoginWindow(self.root, on_success=self.on_login_success)
            print(f"DEBUG: LoginWindow đã tạo: {login_win}")
            print(f"DEBUG: LoginWindow winfo_exists: {login_win.winfo_exists()}")
            login_win.update()  # ===== QUAN TRỌNG: Force update =====
            print(f"DEBUG: LoginWindow winfo_viewable: {login_win.winfo_viewable()}")
            login_win.lift()
            login_win.focus_force()
            print("DEBUG: LoginWindow đã sẵn sàng")
        except Exception as e:
            print(f"DEBUG: Lỗi tạo LoginWindow: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Lỗi", f"Không thể mở cửa sổ đăng nhập: {e}")
            self.root.destroy()

    def on_login_success(self, username: str):
        """Callback khi đăng nhập thành công"""
        print(f"✅ Đăng nhập thành công: {username}")
        
        # ===== Ẩn root nhỏ đi =====
        self.root.withdraw()
        
        # Tạo AdminWindow
        self.admin_window = AdminWindow(self.root, username)
        
        # Xử lý khi đóng
        self.admin_window.protocol("WM_DELETE_WINDOW", self.on_admin_close)

    def on_admin_close(self):
        """Khi cửa sổ admin bị đóng"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn thoát?"):
            print("👋 Đóng ứng dụng Admin.")
            self.root.destroy()

def main():
    """Hàm chạy chính"""
    
    # 1. Kiểm tra thư viện Face Recognition
    try:
        ensure_face_lib()
        print("✅ Thư viện face_recognition đã sẵn sàng")
    except Exception as e:
        messagebox.showerror(
            "Lỗi nghiêm trọng", 
            f"Không tải được face_recognition:\n\n{e}\n\n"
            f"Vui lòng cài đặt:\npip install face-recognition"
        )
        return

    # 2. Kiểm tra kết nối và khởi tạo CSDL
    try:
        db.init_db()
    except Exception as e:
        messagebox.showerror(
            "Lỗi CSDL", 
            f"Không thể kết nối hoặc khởi tạo CSDL:\n\n{e}\n\n"
            f"Vui lòng kiểm tra:\n"
            f"- MySQL Server đã chạy\n"
            f"- Thông tin kết nối trong config.py"
        )
        return

    # 3. Khởi chạy ứng dụng
    try:
        root = tk.Tk()
        root.title("Face Attendance")
        
        app = AdminAppController(root)
        
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Lỗi không xác định", f"Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()