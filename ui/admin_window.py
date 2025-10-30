# Tên file: ui/admin_window.py
# (Đặt ở thư mục ui/)

import tkinter as tk
from tkinter import ttk, messagebox

from config import APP_TITLE
from ui.employee_tab import EmployeeTab
from ui.report_tab import ReportTab
from ui.leave_tab import LeaveTab 
# (Chúng ta vẫn cần tạo file leave_tab.py)

class AdminWindow(tk.Toplevel): # <-- THAY ĐỔI 1: Kế thừa từ Toplevel
    """
    Lớp cửa sổ chính cho Ứng dụng Quản lý (Admin).
    Chỉ được tạo SAU KHI đăng nhập thành công.
    """
    def __init__(self, master, username: str): # <-- THAY ĐỔI 2: Nhận 'master'
        super().__init__(master) # <-- THAY ĐỔI 3: Gọi super()

        # ===== Cấu hình cơ bản & style =====
        # Đặt tiêu đề chào mừng
        self.title(f"{APP_TITLE} - Quản trị (Chào {username})")
        self.geometry("980x680")
        self.resizable(True, True)
        
        # Khi cửa sổ này được tạo, nó sẽ hiện lên
        self.deiconify() 

        # (Toàn bộ code style giữ nguyên y như cũ...)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background="#dbeafe", borderwidth=2)
        style.configure("TNotebook.Tab",
                        background="#bfdbfe", foreground="#0f172a",
                        padding=[10, 5], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#60a5fa")],
                  foreground=[("selected", "black")])
        style.configure("TButton", font=("Segoe UI", 10, "bold"),
                        background="#3b82f6", foreground="white", padding=6)
        style.map("TButton",
                  background=[("active", "#2563eb"), ("disabled", "#db1919")])
        style.configure("TFrame", background="#e8f0fe")
        style.configure("TLabelframe", background="#e8f0fe", 
                        font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background="#e8f0fe")
        style.configure("TLabel", background="#e8f0fe", font=("Segoe UI", 10))


        # ===== Notebook & Tabs =====
        self.nb = ttk.Notebook(self)
        
        self.tab_emp = EmployeeTab(self.nb)
        self.tab_leave = LeaveTab(self.nb)
        self.tab_rep = ReportTab(self.nb)

        self.nb.add(self.tab_emp, text="👥 Nhân viên")
        self.nb.add(self.tab_leave, text="🗓️ Nghỉ phép")
        self.nb.add(self.tab_rep, text="📊 Báo cáo")
        
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)

        # ===== THAY ĐỔI 4: XÓA BỎ TOÀN BỘ LOGIC LOGIN =====
        # Toàn bộ các hàm:
        # _trigger_initial_login()
        # _on_tab_changed()
        # _unlock_tabs()
        # ... ĐỀU ĐÃ ĐƯỢC XÓA BỎ.
        # Lý do: Cửa sổ này giờ đã được xác thực, không cần chặn tab nữa.

        # ===== Đóng cửa sổ =====
        # Hàm on_close() ở file cũ đã được chuyển
        # sang AdminAppController trong main_admin.py
        # nên ở đây không cần self.protocol() nữa.