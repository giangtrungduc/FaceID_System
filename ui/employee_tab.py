import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image

from services import db
from services.face import face_encode_from_image


class EmployeeTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        # List panel
        list_frame = ttk.Frame(self)
        list_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        ttk.Label(list_frame, text="Danh sách nhân viên").pack(anchor="w")
        # thêm cột phone
        self.tree = ttk.Treeview(
            list_frame,
            columns=("id", "code", "name", "dept", "phone"),
            show="headings",
            height=22,
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("code", text="Mã NV")
        self.tree.heading("name", text="Họ tên")
        self.tree.heading("dept", text="Phòng ban")
        self.tree.heading("phone", text="SĐT")
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("code", width=100)
        self.tree.column("name", width=180)
        self.tree.column("dept", width=120)
        self.tree.column("phone", width=110)
        self.tree.pack(fill="both", expand=True)

        btns = ttk.Frame(list_frame)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Tải lại", command=self.refresh_employees).pack(side="left", padx=4)
        ttk.Button(btns, text="Xoá nhân viên đã chọn", command=self.delete_selected_employee).pack(side="left", padx=4)

        # Add form
        form = ttk.LabelFrame(self, text="Thêm nhân viên mới")
        form.pack(side="right", fill="y", padx=10, pady=10)

        self.emp_code_var = tk.StringVar()
        self.emp_name_var = tk.StringVar()
        self.emp_dept_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.face_path_var = tk.StringVar()

        ttk.Label(form, text="Mã nhân viên").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(form, textvariable=self.emp_code_var, width=26).grid(row=0, column=1, padx=6, pady=4)

        ttk.Label(form, text="Họ tên").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(form, textvariable=self.emp_name_var, width=26).grid(row=1, column=1, padx=6, pady=4)

        ttk.Label(form, text="Phòng ban").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(form, textvariable=self.emp_dept_var, width=26).grid(row=2, column=1, padx=6, pady=4)

        ttk.Label(form, text="Số điện thoại").grid(row=3, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(form, textvariable=self.phone_var, width=26).grid(row=3, column=1, padx=6, pady=4)

        ttk.Label(form, text="Ảnh khuôn mặt (jpg/png)").grid(row=4, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(form, textvariable=self.face_path_var, width=26).grid(row=4, column=1, padx=6, pady=4)
        ttk.Button(form, text="Chọn ảnh...", command=self.browse_face_image).grid(row=4, column=2, padx=6, pady=4)

        ttk.Button(form, text="Lưu nhân viên", command=self.save_employee_from_file).grid(row=5, column=1, pady=10)

        for i in range(6):
            form.grid_rowconfigure(i, weight=0)
        form.grid_columnconfigure(1, weight=1)

        self.refresh_employees()

    def refresh_employees(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        df = db.load_all_embeddings()
        if df.empty:
            return
        # map thêm phone nếu có
        phone_series = df.get("phone")
        for _, r in df.iterrows():
            self.tree.insert(
                "",
                "end",
                values=(
                    int(r["id"]),
                    r["emp_code"],
                    r["name"],
                    r["department"],
                    (r["phone"] if phone_series is not None else ""),
                ),
            )

    def browse_face_image(self):
        fpath = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if fpath:
            self.face_path_var.set(fpath)

    def save_employee_from_file(self):
        code = self.emp_code_var.get().strip()
        name = self.emp_name_var.get().strip()
        dept = self.emp_dept_var.get().strip()
        phone = self.phone_var.get().strip()
        fpath = self.face_path_var.get().strip()

        if not code or not name or not fpath:
            messagebox.showwarning("Thiếu thông tin", "Nhập đủ Mã NV, Họ tên và chọn ảnh.")
            return

        try:
            img = Image.open(fpath).convert("RGB")
            enc = face_encode_from_image(img)
            if enc is None:
                messagebox.showerror("Lỗi", "Không phát hiện được khuôn mặt trong ảnh.")
                return

            # gọi hàm add_employee mới (có tham số phone)
            ok, msg = db.add_employee(code, name, dept, phone, enc)

            if ok:
                messagebox.showinfo("Thành công", msg)
                self.refresh_employees()
                self.emp_code_var.set("")
                self.emp_name_var.set("")
                self.emp_dept_var.set("")
                self.phone_var.set("")
                self.face_path_var.set("")
            else:
                messagebox.showerror("Lỗi", msg)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xử lý: {e}")

    def delete_selected_employee(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        emp_id = int(vals[0])
        if messagebox.askyesno("Xác nhận", f"Xoá nhân viên ID {emp_id}?"):
            db.delete_employee(emp_id)
            self.refresh_employees()
