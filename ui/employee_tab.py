"""
Tab quản lý nhân viên - Có chức năng Thêm/Sửa/Xóa
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import db
from services.face import face_encode_from_image

class EmployeeTab(ttk.Frame):
    """Tab quản lý nhân viên"""
    def __init__(self, master):
        super().__init__(master)

        # ===== TRẠNG THÁI =====
        self._edit_mode = False  # False = Thêm mới, True = Sửa
        self._edit_emp_id = None  # ID nhân viên đang sửa

        # ===== Layout chính: 2 cột =====
        self.columnconfigure(0, weight=3)  # List
        self.columnconfigure(1, weight=1)  # Form
        self.rowconfigure(0, weight=1)

        # ===== Panel danh sách (Bên trái) =====
        list_frame = ttk.LabelFrame(self, text="📋 Danh sách nhân viên", padding=10)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Treeview
        cols = ("id", "code", "name", "dept", "phone")
        self.tree = ttk.Treeview(
            list_frame,
            columns=cols,
            show="headings",
            height=25,
        )
        
        self.tree.heading("id", text="ID")
        self.tree.heading("code", text="Mã NV")
        self.tree.heading("name", text="Họ tên")
        self.tree.heading("dept", text="Phòng ban")
        self.tree.heading("phone", text="SĐT")
        
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("code", width=100)
        self.tree.column("name", width=200)
        self.tree.column("dept", width=150)
        self.tree.column("phone", width=120)
        
        self.tree.grid(row=0, column=0, sticky="nsew")

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
            command=self.refresh_employees
        ).pack(side="left", padx=4)
        
        ttk.Button(
            btn_frame, 
            text="✏️ Sửa nhân viên đã chọn", 
            command=self.edit_selected_employee
        ).pack(side="left", padx=4)
        
        ttk.Button(
            btn_frame, 
            text="🗑️ Xóa nhân viên đã chọn", 
            command=self.delete_selected_employee
        ).pack(side="left", padx=4)

        # ===== Panel form (Bên phải) =====
        self.form_frame = ttk.LabelFrame(self, text="➕ Thêm nhân viên mới", padding=15)
        self.form_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        self.emp_code_var = tk.StringVar()
        self.emp_name_var = tk.StringVar()
        self.emp_dept_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.face_path_var = tk.StringVar()

        # Form fields
        row = 0
        
        ttk.Label(self.form_frame, text="Mã nhân viên: *").grid(
            row=row, column=0, sticky="w", pady=6
        )
        self.emp_code_entry = ttk.Entry(
            self.form_frame, 
            textvariable=self.emp_code_var, 
            width=28
        )
        self.emp_code_entry.grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        row += 1

        ttk.Label(self.form_frame, text="Họ và tên: *").grid(
            row=row, column=0, sticky="w", pady=6
        )
        ttk.Entry(self.form_frame, textvariable=self.emp_name_var, width=28).grid(
            row=row, column=1, columnspan=2, sticky="ew", pady=6
        )
        row += 1

        ttk.Label(self.form_frame, text="Phòng ban:").grid(
            row=row, column=0, sticky="w", pady=6
        )
        ttk.Entry(self.form_frame, textvariable=self.emp_dept_var, width=28).grid(
            row=row, column=1, columnspan=2, sticky="ew", pady=6
        )
        row += 1

        ttk.Label(self.form_frame, text="Số điện thoại:").grid(
            row=row, column=0, sticky="w", pady=6
        )
        ttk.Entry(self.form_frame, textvariable=self.phone_var, width=28).grid(
            row=row, column=1, columnspan=2, sticky="ew", pady=6
        )
        row += 1

        ttk.Label(self.form_frame, text="Ảnh khuôn mặt: *").grid(
            row=row, column=0, sticky="w", pady=6
        )
        ttk.Entry(
            self.form_frame, 
            textvariable=self.face_path_var, 
            width=20,
            state="readonly"
        ).grid(row=row, column=1, sticky="ew", pady=6)
        
        ttk.Button(
            self.form_frame, 
            text="📁", 
            command=self.browse_face_image,
            width=3
        ).grid(row=row, column=2, padx=(5, 0), pady=6)
        row += 1

        # Note
        self.note_label = ttk.Label(
            self.form_frame,
            text="* Bắt buộc khi thêm mới\n\nLưu ý: Ảnh khuôn mặt cần:\n"
                 "- Rõ nét, nhìn thẳng\n"
                 "- Ánh sáng tốt\n"
                 "- Chỉ 1 người trong ảnh",
            foreground="#64748b",
            font=("Segoe UI", 9)
        )
        self.note_label.grid(row=row, column=0, columnspan=3, sticky="w", pady=(10, 10))
        row += 1

        # Save button
        self.save_button = ttk.Button(
            self.form_frame, 
            text="💾 Lưu nhân viên", 
            command=self.save_employee
        )
        self.save_button.grid(row=row, column=0, columnspan=3, pady=(5, 0), sticky="ew")
        row += 1

        # Cancel button (chỉ hiện khi đang sửa)
        self.cancel_button = ttk.Button(
            self.form_frame,
            text="❌ Hủy",
            command=self.cancel_edit
        )
        # Không grid ngay, chỉ hiện khi edit

        self.form_frame.columnconfigure(1, weight=1)

        # Load data lần đầu
        self.after(100, self.refresh_employees)

    def refresh_employees(self):
        """Tải lại danh sách nhân viên"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        try:
            df = db.get_all_employees()
            if df.empty:
                return
            
            for _, row in df.iterrows():
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        int(row["id"]),
                        row["emp_code"],
                        row["name"],
                        row.get("department", ""),
                        row.get("phone", ""),
                    ),
                )
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách nhân viên: {e}")

    def browse_face_image(self):
        """Chọn file ảnh khuôn mặt"""
        fpath = filedialog.askopenfilename(
            title="Chọn ảnh khuôn mặt",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png"),
                ("All files", "*.*")
            ]
        )
        if fpath:
            self.face_path_var.set(fpath)

    def edit_selected_employee(self):
        """Chuyển sang chế độ sửa nhân viên đã chọn"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(
                "Chưa chọn", 
                "Vui lòng chọn nhân viên cần sửa."
            )
            return
        
        vals = self.tree.item(sel[0], "values")
        emp_id = int(vals[0])
        
        # Lấy thông tin chi tiết
        try:
            emp = db.get_employee_by_id(emp_id)
            if not emp:
                messagebox.showerror("Lỗi", "Không tìm thấy nhân viên.")
                return
            
            # Chuyển sang chế độ sửa
            self._edit_mode = True
            self._edit_emp_id = emp_id
            
            # Đổi title form
            self.form_frame.config(text=f"✏️ Sửa nhân viên: {emp['emp_code']}")
            
            # Điền thông tin vào form
            self.emp_code_var.set(emp['emp_code'])
            self.emp_name_var.set(emp['name'])
            self.emp_dept_var.set(emp.get('department', ''))
            self.phone_var.set(emp.get('phone', ''))
            self.face_path_var.set("")  # Để trống, nếu không chọn ảnh mới = giữ nguyên
            
            # Disable mã NV (không cho sửa)
            self.emp_code_entry.config(state="disabled")
            
            # Thay đổi note
            self.note_label.config(
                text="📝 Chế độ SỬA:\n\n"
                     "• Mã NV không thể thay đổi\n"
                     "• Nếu không chọn ảnh mới,\n"
                     "  hệ thống sẽ giữ nguyên ảnh cũ\n"
                     "• Các trường khác có thể sửa"
            )
            
            # Đổi text nút
            self.save_button.config(text="💾 Cập nhật")
            
            # Hiện nút Hủy
            self.cancel_button.grid(row=7, column=0, columnspan=3, pady=(5, 0), sticky="ew")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải thông tin nhân viên: {e}")

    def cancel_edit(self):
        """Hủy chế độ sửa, quay về thêm mới"""
        self._edit_mode = False
        self._edit_emp_id = None
        
        # Đổi title
        self.form_frame.config(text="➕ Thêm nhân viên mới")
        
        # Clear form
        self.emp_code_var.set("")
        self.emp_name_var.set("")
        self.emp_dept_var.set("")
        self.phone_var.set("")
        self.face_path_var.set("")
        
        # Enable lại mã NV
        self.emp_code_entry.config(state="normal")
        
        # Đổi note
        self.note_label.config(
            text="* Bắt buộc khi thêm mới\n\nLưu ý: Ảnh khuôn mặt cần:\n"
                 "- Rõ nét, nhìn thẳng\n"
                 "- Ánh sáng tốt\n"
                 "- Chỉ 1 người trong ảnh"
        )
        
        # Đổi text nút
        self.save_button.config(text="💾 Lưu nhân viên")
        
        # Ẩn nút Hủy
        self.cancel_button.grid_forget()

    def save_employee(self):
        """Lưu nhân viên (Thêm mới hoặc Cập nhật)"""
        if self._edit_mode:
            self._update_employee()
        else:
            self._add_new_employee()

    def _add_new_employee(self):
        """Thêm nhân viên mới"""
        code = self.emp_code_var.get().strip()
        name = self.emp_name_var.get().strip()
        dept = self.emp_dept_var.get().strip()
        phone = self.phone_var.get().strip()
        fpath = self.face_path_var.get().strip()

        if not code or not name or not fpath:
            messagebox.showwarning(
                "Thiếu thông tin", 
                "Vui lòng nhập đủ:\n- Mã nhân viên\n- Họ tên\n- Ảnh khuôn mặt"
            )
            return

        try:
            # Load và encode ảnh
            img = Image.open(fpath).convert("RGB")
            enc = face_encode_from_image(img)
            
            if enc is None:
                messagebox.showerror(
                    "Lỗi nhận diện", 
                    "Không phát hiện được khuôn mặt trong ảnh.\n\n"
                    "Vui lòng chọn ảnh khác với:\n"
                    "- Khuôn mặt rõ ràng\n"
                    "- Ánh sáng tốt\n"
                    "- Chỉ 1 người"
                )
                return

            # Lưu vào database
            ok, msg = db.add_employee(code, name, dept, phone, enc)

            if ok:
                messagebox.showinfo("Thành công", msg)
                self.refresh_employees()
                # Clear form
                self.emp_code_var.set("")
                self.emp_name_var.set("")
                self.emp_dept_var.set("")
                self.phone_var.set("")
                self.face_path_var.set("")
            else:
                messagebox.showerror("Lỗi", msg)
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xử lý: {e}")

    def _update_employee(self):
        """Cập nhật thông tin nhân viên"""
        name = self.emp_name_var.get().strip()
        dept = self.emp_dept_var.get().strip()
        phone = self.phone_var.get().strip()
        fpath = self.face_path_var.get().strip()

        if not name:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập họ tên.")
            return

        try:
            # Kiểm tra có chọn ảnh mới không
            enc = None
            if fpath:
                img = Image.open(fpath).convert("RGB")
                enc = face_encode_from_image(img)
                
                if enc is None:
                    messagebox.showerror(
                        "Lỗi nhận diện", 
                        "Không phát hiện được khuôn mặt trong ảnh mới.\n\n"
                        "Vui lòng chọn ảnh khác hoặc bỏ trống để giữ ảnh cũ."
                    )
                    return

            # Cập nhật database
            ok, msg = db.update_employee(self._edit_emp_id, name, dept, phone, enc)

            if ok:
                messagebox.showinfo("Thành công", msg)
                self.refresh_employees()
                self.cancel_edit()  # Quay về chế độ thêm mới
            else:
                messagebox.showerror("Lỗi", msg)
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xử lý: {e}")

    def delete_selected_employee(self):
        """Xóa nhân viên đã chọn"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(
                "Chưa chọn", 
                "Vui lòng chọn nhân viên cần xóa."
            )
            return
        
        vals = self.tree.item(sel[0], "values")
        emp_id = int(vals[0])
        emp_name = vals[2]
        
        if messagebox.askyesno(
            "Xác nhận xóa", 
            f"Bạn có chắc muốn xóa nhân viên:\n\n"
            f"ID: {emp_id}\n"
            f"Tên: {emp_name}\n\n"
            f"⚠️ Thao tác này không thể hoàn tác!"
        ):
            try:
                db.delete_employee(emp_id)
                messagebox.showinfo("Thành công", "Đã xóa nhân viên.")
                self.refresh_employees()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")