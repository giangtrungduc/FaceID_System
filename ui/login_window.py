"""
Dialog đăng nhập cho Admin
"""

import tkinter as tk
from tkinter import ttk, messagebox

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import db

class LoginWindow(tk.Toplevel):
    """Cửa sổ đăng nhập"""
    def __init__(self, master, on_success):
        super().__init__(master)
        
        # ===== CẤU HÌNH CƠ BẢN =====
        self.title("🔐 Đăng nhập Admin")
        self.resizable(False, False)
        
        # ===== QUAN TRỌNG: Thiết lập geometry TRƯỚC transient =====
        window_width = 380
        window_height = 240
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # ===== SAU ĐÓ MỚI transient và grab_set =====
        self.transient(master)
        self.grab_set()

        # ===== GIAO DIỆN =====
        # Background
        self.configure(bg="#f0f4f8")
        
        main_frame = tk.Frame(self, bg="#ffffff", relief="raised", borderwidth=2)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        frm = tk.Frame(main_frame, bg="#ffffff", padx=20, pady=20)
        frm.pack(fill="both", expand=True)

        # Title
        title_label = tk.Label(
            frm, 
            text="🔐 Đăng nhập Quản trị",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#1e40af"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 25))

        # Username
        tk.Label(
            frm, 
            text="Tên đăng nhập:",
            font=("Segoe UI", 10),
            bg="#ffffff"
        ).grid(row=1, column=0, sticky="w", pady=8)
        
        self._u = tk.StringVar()
        username_entry = tk.Entry(
            frm, 
            textvariable=self._u, 
            width=28,
            font=("Segoe UI", 10),
            relief="solid",
            borderwidth=1
        )
        username_entry.grid(row=1, column=1, sticky="ew", pady=8, padx=(10, 0))

        # Password
        tk.Label(
            frm,
            text="Mật khẩu:",
            font=("Segoe UI", 10),
            bg="#ffffff"
        ).grid(row=2, column=0, sticky="w", pady=8)
        
        self._p = tk.StringVar()
        password_entry = tk.Entry(
            frm, 
            textvariable=self._p, 
            show="●", 
            width=28,
            font=("Segoe UI", 10),
            relief="solid",
            borderwidth=1
        )
        password_entry.grid(row=2, column=1, sticky="ew", pady=8, padx=(10, 0))

        # Button frame
        btn_frame = tk.Frame(frm, bg="#ffffff")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(25, 0))

        login_btn = tk.Button(
            btn_frame, 
            text="Đăng nhập", 
            command=self._login,
            width=15,
            font=("Segoe UI", 10, "bold"),
            bg="#3b82f6",
            fg="white",
            relief="raised",
            borderwidth=2,
            cursor="hand2"
        )
        login_btn.pack(side="left", padx=5)

        cancel_btn = tk.Button(
            btn_frame,
            text="Thoát",
            command=self._on_cancel,
            width=15,
            font=("Segoe UI", 10),
            bg="#e5e7eb",
            fg="#374151",
            relief="raised",
            borderwidth=2,
            cursor="hand2"
        )
        cancel_btn.pack(side="left", padx=5)

        frm.columnconfigure(1, weight=1)

        # Bind Enter key
        self.bind("<Return>", lambda e: self._login())
        self.bind("<Escape>", lambda e: self._on_cancel())
        
        # ===== QUAN TRỌNG: Focus và hiển thị =====
        self.update_idletasks()  # Cập nhật geometry
        username_entry.focus_set()
        
        # Đưa cửa sổ lên trên cùng
        self.lift()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        # ===== FORCE UPDATE =====
        self.update()

        self._on_success = on_success

    def _login(self):
        """Xử lý đăng nhập"""
        u = self._u.get().strip()
        p = self._p.get().strip()
        
        if not u or not p:
            messagebox.showwarning(
                "Thiếu thông tin", 
                "Vui lòng nhập đủ tên đăng nhập và mật khẩu.",
                parent=self
            )
            return
        
        try:
            if db.check_login(u, p):
                self._on_success(username=u)
                self.destroy()
            else:
                messagebox.showerror(
                    "Đăng nhập thất bại", 
                    "Tên đăng nhập hoặc mật khẩu không đúng.",
                    parent=self
                )
                self._p.set("")
                self.after(100, lambda: self.lift())
        except Exception as e:
            messagebox.showerror(
                "Lỗi", 
                f"Không kiểm tra được đăng nhập: {e}",
                parent=self
            )

    def _on_cancel(self):
        """Xử lý khi nhấn Thoát"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn thoát?", parent=self):
            self.destroy()
            self.master.destroy()