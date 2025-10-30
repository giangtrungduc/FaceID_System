# Tên file: ui/admin_window.py
"""
Cửa sổ chính cho Ứng dụng Quản lý (Admin)
"""

import tkinter as tk
from tkinter import ttk

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import APP_TITLE, APP_VERSION
from .employee_tab import EmployeeTab
from .report_tab import ReportTab
from .leave_tab import LeaveTab

class AdminWindow(tk.Toplevel):
    """
    Lớp cửa sổ chính cho Ứng dụng Quản lý (Admin).
    Chỉ được tạo SAU KHI đăng nhập thành công.
    """
    def __init__(self, master, username: str):
        super().__init__(master)

        # ===== Cấu hình cơ bản & style =====
        self.title(f"{APP_TITLE} v{APP_VERSION} - Quản trị viên: {username}")
        self.geometry("1024x768")
        self.resizable(True, True)
        
        self.deiconify()

        # Style configuration
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
                  background=[("active", "#2563eb"), ("disabled", "#94a3b8")])
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