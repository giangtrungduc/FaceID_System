# Tên file: ui/leave_tab.py
# (Đặt ở thư mục ui/)

import tkinter as tk
from tkinter import ttk, messagebox
import datetime as dt

# Cần cài đặt: pip install tkcalendar
try:
    from tkcalendar import DateEntry
except ImportError:
    messagebox.showwarning(
        "Thiếu thư viện", 
        "Vui lòng cài đặt 'tkcalendar' để sử dụng tab này:\n\npip install tkcalendar"
    )
    # Tạo widget giả để chương trình không crash
    class DateEntry: 
        def __init__(self, *args, **kwargs): pass
        def get_date(self): return dt.date.today()

from services import db

class LeaveTab(ttk.Frame):
    """
    Giao diện Tab Quản lý Nghỉ phép.
    """
    def __init__(self, master):
        super().__init__(master)
        
        # Dữ liệu cache
        self._employee_list = {} # { "Tên (Mã NV)": emp_id }

        # Cấu hình layout chính (2 cột: Form bên trái, List bên phải)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # === 1. Khung Form (Bên trái) ===
        form_frame = ttk.LabelFrame(self, text="Duyệt nghỉ phép")
        form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

        ttk.Label(form_frame, text="Chọn nhân viên:").grid(
            row=0, column=0, sticky="w", padx=8, pady=(8, 4))
        
        self.emp_var = tk.StringVar()
        self.emp_combo = ttk.Combobox(
            form_frame, 
            textvariable=self.emp_var, 
            state="readonly",
            width=30
        )
        self.emp_combo.grid(row=1, column=0, columnspan=2, 
                            sticky="ew", padx=8, pady=4)

        ttk.Label(form_frame, text="Ngày nghỉ:").grid(
            row=2, column=0, sticky="w", padx=8, pady=4)
        self.date_entry = DateEntry(
            form_frame, 
            date_pattern='yyyy-mm-dd',
            width=28
        )
        self.date_entry.grid(row=3, column=0, columnspan=2, 
                             sticky="ew", padx=8, pady=4)
        
        ttk.Label(form_frame, text="Lý do (không bắt buộc):").grid(
            row=4, column=0, sticky="w", padx=8, pady=4)
        
        self.reason_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.reason_var, width=32).grid(
            row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        ttk.Button(form_frame, text="Lưu nghỉ phép", command=self._add_leave).grid(
            row=6, column=0, columnspan=2, pady=10)


        # === 2. Khung Danh sách (Bên phải) ===
        list_frame = ttk.LabelFrame(self, text="Danh sách nghỉ phép đã duyệt")
        list_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Treeview
        cols = ("id", "emp_code", "name", "date", "reason")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=20)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("emp_code", text="Mã NV")
        self.tree.heading("name", text="Họ tên")
        self.tree.heading("date", text="Ngày nghỉ")
        self.tree.heading("reason", text="Lý do")
        
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("emp_code", width=80)
        self.tree.column("name", width=150)
        self.tree.column("date", width=100, anchor="center")
        self.tree.column("reason", width=150)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Khung nút
        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=8)

        ttk.Button(btn_frame, text="Tải lại danh sách", command=self._load_data).pack(
            side="left", padx=6)
        ttk.Button(btn_frame, text="Xóa ngày nghỉ đã chọn", command=self._delete_leave).pack(
            side="left", padx=6)

        # Tải dữ liệu lần đầu
        self.after(200, self._load_data)

    def _load_data(self):
        """Tải cả danh sách nhân viên và danh sách nghỉ phép"""
        self._load_employee_list()
        self._load_leave_list()

    def _load_employee_list(self):
        """Tải danh sách nhân viên cho Combobox"""
        try:
            df = db.get_all_employees()
            if df.empty:
                return
            
            # Xóa cache cũ
            self._employee_list.clear()
            
            emp_display_list = []
            for _, row in df.iterrows():
                # Hiển thị "Họ Tên (Mã NV)"
                display_name = f"{row['name']} ({row['emp_code']})"
                self._employee_list[display_name] = int(row['id'])
                emp_display_list.append(display_name)
            
            self.emp_combo['values'] = emp_display_list
            if emp_display_list:
                self.emp_combo.current(0)
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được danh sách nhân viên: {e}")

    def _load_leave_list(self):
        """Tải danh sách nghỉ phép vào Treeview"""
        try:
            # Lấy 1 năm gần nhất
            end_date = dt.date.today()
            start_date = end_date - dt.timedelta(days=365)
            
            df = db.get_leave_records(start_date, end_date)
            
            # Xóa cây
            for i in self.tree.get_children():
                self.tree.delete(i)
            
            if df.empty:
                return
            
            # Đổ dữ liệu
            for _, row in df.iterrows():
                self.tree.insert("", "end", values=(
                    int(row['id']),
                    row['emp_code'],
                    row['emp_name'],
                    str(row['leave_date']),
                    row['reason']
                ))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được danh sách nghỉ phép: {e}")

    def _add_leave(self):
        """Lưu bản ghi nghỉ phép mới"""
        emp_display_name = self.emp_var.get()
        if not emp_display_name:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn nhân viên.")
            return
            
        try:
            emp_id = self._employee_list[emp_display_name]
            leave_date = self.date_entry.get_date()
            reason = self.reason_var.get().strip()
            
            if not reason:
                reason = "Nghỉ phép" # Lý do mặc định

            ok, msg = db.add_leave(emp_id, leave_date, reason)
            
            if ok:
                messagebox.showinfo("Thành công", msg)
                self._load_leave_list() # Tải lại danh sách
                self.reason_var.set("")
            else:
                messagebox.showerror("Lỗi", msg)
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi lưu: {e}")

    def _delete_leave(self):
        """Xóa bản ghi nghỉ phép đã chọn"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một bản ghi để xóa.")
            return
            
        vals = self.tree.item(sel[0], "values")
        leave_id = int(vals[0])
        emp_name = vals[2]
        leave_date = vals[3]
        
        if messagebox.askyesno(
            "Xác nhận", 
            f"Bạn có chắc muốn xóa ngày nghỉ của {emp_name} (ngày {leave_date})?"
        ):
            try:
                ok, msg = db.delete_leave(leave_id)
                if ok:
                    messagebox.showinfo("Thành công", msg)
                    self._load_leave_list()
                else:
                    messagebox.showerror("Lỗi", msg)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi khi xóa: {e}")