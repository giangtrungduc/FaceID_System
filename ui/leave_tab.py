"""
Tab quản lý nghỉ phép
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime as dt

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cần cài đặt: pip install tkcalendar
try:
    from tkcalendar import DateEntry
    _calendar_available = True
except ImportError:
    _calendar_available = False
    # Fallback: Tạo widget giả
    class DateEntry(ttk.Entry):
        def __init__(self, master, **kwargs):
            super().__init__(master, width=12)
        def get_date(self):
            val = self.get()
            try:
                return dt.datetime.strptime(val, "%Y-%m-%d").date()
            except:
                return dt.date.today()

from services import db

class LeaveTab(ttk.Frame):
    """Tab quản lý nghỉ phép"""
    def __init__(self, master):
        super().__init__(master)
        
        # Hiển thị cảnh báo nếu thiếu thư viện
        if not _calendar_available:
            messagebox.showwarning(
                "Thiếu thư viện",
                "Thư viện 'tkcalendar' chưa được cài đặt.\n\n"
                "Chạy lệnh: pip install tkcalendar\n\n"
                "Bạn vẫn có thể sử dụng nhưng phải nhập ngày thủ công."
            )
        
        # Dữ liệu cache
        self._employee_list = {}  # { "Tên (Mã NV)": emp_id }

        # Layout chính
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        # ===== 1. Khung Form (Bên trái) =====
        form_frame = ttk.LabelFrame(self, text="📝 Duyệt nghỉ phép", padding=15)
        form_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")

        row = 0
        
        ttk.Label(form_frame, text="Chọn nhân viên: *").grid(
            row=row, column=0, sticky="w", pady=(0, 4)
        )
        row += 1
        
        self.emp_var = tk.StringVar()
        self.emp_combo = ttk.Combobox(
            form_frame, 
            textvariable=self.emp_var, 
            state="readonly",
            width=32
        )
        self.emp_combo.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        row += 1

        ttk.Label(form_frame, text="Ngày nghỉ: *").grid(
            row=row, column=0, sticky="w", pady=(0, 4)
        )
        row += 1
        
        if _calendar_available:
            self.date_entry = DateEntry(
                form_frame, 
                date_pattern='yyyy-mm-dd',
                width=30
            )
        else:
            self.date_entry = DateEntry(form_frame)
            ttk.Label(
                form_frame,
                text="(Định dạng: YYYY-MM-DD)",
                foreground="#64748b",
                font=("Segoe UI", 8)
            ).grid(row=row+1, column=0, sticky="w")
            
        self.date_entry.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        row += 2
        
        ttk.Label(form_frame, text="Lý do:").grid(
            row=row, column=0, sticky="w", pady=(0, 4)
        )
        row += 1
        
        self.reason_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.reason_var, width=34).grid(
            row=row, column=0, sticky="ew", pady=(0, 20)
        )
        row += 1

        ttk.Button(
            form_frame, 
            text="💾 Lưu nghỉ phép", 
            command=self._add_leave
        ).grid(row=row, column=0, sticky="ew")
        
        form_frame.columnconfigure(0, weight=1)

        # ===== 2. Khung Danh sách (Bên phải) =====
        list_frame = ttk.LabelFrame(self, text="📋 Danh sách nghỉ phép", padding=10)
        list_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Treeview
        cols = ("id", "emp_code", "name", "date", "reason")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=25)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("emp_code", text="Mã NV")
        self.tree.heading("name", text="Họ tên")
        self.tree.heading("date", text="Ngày nghỉ")
        self.tree.heading("reason", text="Lý do")
        
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("emp_code", width=90)
        self.tree.column("name", width=180)
        self.tree.column("date", width=110, anchor="center")
        self.tree.column("reason", width=200)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Buttons
        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        ttk.Button(
            btn_frame, 
            text="🔄 Tải lại", 
            command=self._load_data
        ).pack(side="left", padx=4)
        
        ttk.Button(
            btn_frame, 
            text="🗑️ Xóa ngày nghỉ đã chọn", 
            command=self._delete_leave
        ).pack(side="left", padx=4)

        # Tải dữ liệu lần đầu
        self.after(200, self._load_data)

    def _load_data(self):
        """Tải dữ liệu"""
        self._load_employee_list()
        self._load_leave_list()

    def _load_employee_list(self):
        """Tải danh sách nhân viên cho Combobox"""
        try:
            df = db.get_all_employees()
            if df.empty:
                return
            
            self._employee_list.clear()
            emp_display_list = []
            
            for _, row in df.iterrows():
                display_name = f"{row['name']} ({row['emp_code']})"
                self._employee_list[display_name] = int(row['id'])
                emp_display_list.append(display_name)
            
            self.emp_combo['values'] = emp_display_list
            if emp_display_list:
                self.emp_combo.current(0)
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được danh sách nhân viên: {e}")

    def _load_leave_list(self):
        """Tải danh sách nghỉ phép"""
        try:
            # Lấy 1 năm gần nhất
            end_date = dt.date.today()
            start_date = end_date - dt.timedelta(days=365)
            
            df = db.get_leave_records(start_date, end_date)
            
            # Xóa dữ liệu cũ
            for i in self.tree.get_children():
                self.tree.delete(i)
            
            if df.empty:
                return
            
            # Đổ dữ liệu mới
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
                reason = "Nghỉ phép"

            ok, msg = db.add_leave(emp_id, leave_date, reason)
            
            if ok:
                messagebox.showinfo("Thành công", msg)
                self._load_leave_list()
                self.reason_var.set("")
            else:
                messagebox.showerror("Lỗi", msg)
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi lưu: {e}")

    def _delete_leave(self):
        """Xóa bản ghi nghỉ phép"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn bản ghi cần xóa.")
            return
            
        vals = self.tree.item(sel[0], "values")
        leave_id = int(vals[0])
        emp_name = vals[2]
        leave_date = vals[3]
        
        if messagebox.askyesno(
            "Xác nhận xóa", 
            f"Xóa ngày nghỉ phép của:\n\n"
            f"Nhân viên: {emp_name}\n"
            f"Ngày: {leave_date}\n\n"
            f"⚠️ Thao tác này không thể hoàn tác!"
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