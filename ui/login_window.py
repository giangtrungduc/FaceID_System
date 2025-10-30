import tkinter as tk
from tkinter import ttk, messagebox
from services import db

class LoginWindow(tk.Toplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.title("Đăng nhập")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # ==== Căn giữa cửa sổ đăng nhập ====
        self.update_idletasks()
        window_width = 320
        window_height = 180
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Tên đăng nhập").grid(row=0, column=0, sticky="w", pady=4)
        self._u = tk.StringVar()
        ttk.Entry(frm, textvariable=self._u).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Mật khẩu").grid(row=1, column=0, sticky="w", pady=4)
        self._p = tk.StringVar()
        ttk.Entry(frm, textvariable=self._p, show="*").grid(row=1, column=1, sticky="ew", pady=4)

        btn = ttk.Button(frm, text="Đăng nhập", command=self._login)
        btn.grid(row=2, column=1, sticky="e", pady=8)

        frm.columnconfigure(1, weight=1)
        self._on_success = on_success

    def _login(self):
        u = self._u.get().strip()
        p = self._p.get().strip()
        if not u or not p:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đủ tên đăng nhập và mật khẩu.")
            return
        try:
            if db.check_login(u, p):
                self._on_success(username=u)
                self.destroy()
            else:
                messagebox.showerror("Sai thông tin", "Tên đăng nhập hoặc mật khẩu không đúng.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không kiểm tra được đăng nhập: {e}")
