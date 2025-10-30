# Tên file: main_admin.py
# (Đặt ở thư mục gốc)

import tkinter as tk
from tkinter import messagebox
from services import db
from services.face import ensure_face_lib

# Import 2 cửa sổ
from ui.login_window import LoginWindow
from ui.admin_window import AdminWindow

class AdminAppController:
    """
    Class này quản lý luồng:
    1. Mở LoginWindow
    2. Nếu thành công -> Mở AdminWindow
    """
    def __init__(self, root):
        self.root = root
        self.root.withdraw() # Ẩn cửa sổ root
        
        # 1. Mở LoginWindow trước
        # Cửa sổ này sẽ modal, app sẽ dừng ở đây
        # Khi LoginWindow đóng, nó sẽ gọi self.on_login_attempt
        LoginWindow(self.root, on_success=self.on_login_success)

    def on_login_success(self, username: str):
        """
        Được gọi khi LoginWindow xác thực thành công.
        """
        print(f"Đăng nhập thành công với tư cách {username}")
        
        # 2. Tạo và hiển thị AdminWindow
        # (LoginWindow đã tự hủy)
        
        # Tạo AdminWindow (lưu ý: AdminWindow giờ là Toplevel)
        self.admin_window = AdminWindow(self.root, username)
        
        # Khi AdminWindow đóng, chúng ta sẽ tắt toàn bộ app
        self.admin_window.protocol("WM_DELETE_WINDOW", self.on_admin_close)

    def on_admin_close(self):
        """Khi cửa sổ admin chính bị đóng."""
        print("Đóng ứng dụng Admin.")
        self.root.destroy()

def main():
    """Hàm chạy chính cho Ứng dụng Quản lý (Admin)."""
    
    # 1. Kiểm tra thư viện Face Recognition
    try:
        ensure_face_lib()
    except Exception as e:
        messagebox.showerror("Lỗi nghiêm trọng", f"Không tải được face_recognition: {e}")
        return

    # 2. Kiểm tra kết nối và khởi tạo CSDL
    try:
        db.init_db()
    except Exception as e:
        messagebox.showerror("Lỗi CSDL", f"Không thể kết nối hoặc khởi tạo CSDL: {e}")
        return

    # 3. Khởi chạy luồng ứng dụng
    try:
        root = tk.Tk()
        app = AdminAppController(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Lỗi không xác định", f"Lỗi: {e}")

if __name__ == "__main__":
    main()