# Tên file: ui/report_tab.py
# (Đặt ở thư mục ui/)

import datetime as dt
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

from services import db

# (Tùy chọn) Giờ vào làm mặc định để check đi muộn
DEFAULT_WORK_START_TIME = dt.time(8, 30, 0)

class ReportTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        # === 1. Khung Lọc (Bên trên) ===
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Từ ngày (YYYY-MM-DD):").pack(side="left")
        self.start_var = tk.StringVar(value=str(dt.date.today().replace(day=1)))
        ttk.Entry(top, textvariable=self.start_var, width=12).pack(side="left", padx=6)

        ttk.Label(top, text="Đến ngày (YYYY-MM-DD):").pack(side="left")
        self.end_var = tk.StringVar(value=str(dt.date.today()))
        ttk.Entry(top, textvariable=self.end_var, width=12).pack(side="left", padx=6)

        ttk.Button(top, text="📊 Lấy dữ liệu", command=self.load_reports).pack(side="left", padx=6)
        ttk.Button(top, text="Xuất CSV (Chi tiết)", command=self.export_daily_csv).pack(side="left", padx=6)
        ttk.Button(top, text="Xuất CSV (Tổng hợp)", command=self.export_total_csv).pack(side="left", padx=6)

        # === 2. Báo cáo Chi tiết (Giữa) ===
        ttk.Label(self, text="Báo cáo chi tiết (Từng nhân viên theo từng ngày)").pack(anchor="w", padx=10)
        
        # Cột mới: Thêm "Trạng thái"
        cols_daily = ("emp_code", "name", "department", "date", 
                      "status", "first_in", "last_out", "hours")
        
        self.tree_daily = ttk.Treeview(self, columns=cols_daily, show="headings", height=10)
        
        self.tree_daily.heading("emp_code", text="Mã NV")
        self.tree_daily.heading("name", text="Họ tên")
        self.tree_daily.heading("department", text="Phòng ban")
        self.tree_daily.heading("date", text="Ngày")
        self.tree_daily.heading("status", text="Trạng thái")
        self.tree_daily.heading("first_in", text="Vào đầu")
        self.tree_daily.heading("last_out", text="Ra cuối")
        self.tree_daily.heading("hours", text="Giờ làm")
        
        self.tree_daily.column("emp_code", width=80, anchor="center")
        self.tree_daily.column("name", width=150)
        self.tree_daily.column("department", width=100)
        self.tree_daily.column("date", width=100, anchor="center")
        self.tree_daily.column("status", width=100, anchor="center")
        self.tree_daily.column("first_in", width=120, anchor="center")
        self.tree_daily.column("last_out", width=120, anchor="center")
        self.tree_daily.column("hours", width=60, anchor="center")
        
        self.tree_daily.pack(fill="x", expand=True, padx=10, pady=6)

        # === 3. Báo cáo Tổng hợp (Dưới) ===
        ttk.Label(self, text="Báo cáo tổng hợp (Theo nhân viên)").pack(anchor="w", padx=10)
        
        # Cột mới: Ngày công, Ngày vắng, Ngày phép
        cols_total = ("emp_code", "name", "department", 
                      "days_present", "days_leave", "days_absent", "total_hours")
                      
        self.tree_total = ttk.Treeview(self, columns=cols_total, show="headings", height=10)
        
        self.tree_total.heading("emp_code", text="Mã NV")
        self.tree_total.heading("name", text="Họ tên")
        self.tree_total.heading("department", text="Phòng ban")
        self.tree_total.heading("days_present", text="Ngày công")
        self.tree_total.heading("days_leave", text="Ngày phép")
        self.tree_total.heading("days_absent", text="Ngày vắng")
        self.tree_total.heading("total_hours", text="Tổng giờ làm")
        
        self.tree_total.column("emp_code", width=80, anchor="center")
        self.tree_total.column("name", width=150)
        self.tree_total.column("department", width=100)
        self.tree_total.column("days_present", width=80, anchor="center")
        self.tree_total.column("days_leave", width=80, anchor="center")
        self.tree_total.column("days_absent", width=80, anchor="center")
        self.tree_total.column("total_hours", width=100, anchor="center")
        
        self.tree_total.pack(fill="x", expand=True, padx=10, pady=6)

        # Dữ liệu DataFrame để xuất CSV
        self._daily_df = None
        self._total_df = None

    def parse_date(self, s: str):
        try:
            return dt.datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            return None

    def _populate_tree(self, tree: ttk.Treeview, df: pd.DataFrame):
        """Xóa cây và đổ dữ liệu từ DataFrame"""
        for i in tree.get_children():
            tree.delete(i)
        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))

    def _apply_status(self, row):
        """Hàm logic để xác định trạng thái cuối cùng"""
        # Ưu tiên 1: Nghỉ phép
        if pd.notna(row['leave_date']):
            return "Nghỉ phép"
        
        # Ưu tiên 2: Có mặt (có giờ làm)
        if pd.notna(row['hours']) and row['hours'] > 0:
            # (Tùy chọn) Kiểm tra đi muộn
            if pd.notna(row['first_in']) and row['first_in'].time() > DEFAULT_WORK_START_TIME:
                return "Đi muộn"
            return "Có mặt"
        
        # Ưu tiên 3: Vắng
        # (Nếu không nghỉ phép và không có giờ làm)
        return "Vắng"

    def load_reports(self):
        """
        Logic cốt lõi: Tải và tổng hợp 3 nguồn dữ liệu
        (Nhân viên, Chấm công, Nghỉ phép)
        """
        s = self.parse_date(self.start_var.get().strip())
        e = self.parse_date(self.end_var.get().strip())
        if s is None or e is None:
            messagebox.showwarning("Sai định dạng", "Ngày phải theo định dạng YYYY-MM-DD.")
            return
        if e < s:
            messagebox.showwarning("Lỗi", "Ngày kết thúc phải sau ngày bắt đầu.")
            return

        try:
            # === 1. Tải 3 nguồn dữ liệu ===
            # Nguồn 1: Danh sách nhân viên
            all_emps_df = db.get_all_employees()
            if all_emps_df.empty:
                messagebox.showinfo("Thông báo", "Không có nhân viên nào trong hệ thống.")
                return
            
            # Nguồn 2: Dữ liệu chấm công (đã tính toán)
            att_raw_df = db.get_attendance(s, e)
            work_hours_df = db.compute_work_hours(att_raw_df)
            
            # Nguồn 3: Dữ liệu nghỉ phép
            leave_df = db.get_leave_records(s, e)
            # Chuyển đổi cột 'leave_date' sang datetime để join
            if not leave_df.empty:
                leave_df['leave_date'] = pd.to_datetime(leave_df['leave_date'])
            
            # === 2. Tạo Bảng chấm công đầy đủ ===
            # Tạo 1 hàng cho mỗi nhân viên, mỗi ngày
            all_days = pd.to_datetime(pd.date_range(s, e, freq='D'))
            
            # (emp_id) x (date) -> Tạo bảng base
            base_df = all_emps_df[['id', 'emp_code', 'name', 'department']].copy()
            base_df['key'] = 1
            days_df = pd.DataFrame({'date': all_days, 'key': 1})
            
            daily_report_df = pd.merge(base_df, days_df, on='key').drop('key', axis=1)
            daily_report_df = daily_report_df.rename(columns={'id': 'emp_id'})

            # === 3. Ghép (Merge) dữ liệu ===
            
            # Ghép dữ liệu giờ làm (đã tính)
            if not work_hours_df.empty:
                work_hours_df['date'] = pd.to_datetime(work_hours_df['date'])
                daily_report_df = pd.merge(
                    daily_report_df,
                    work_hours_df[['emp_id', 'date', 'first_in', 'last_out', 'hours']],
                    on=['emp_id', 'date'],
                    how='left'
                )
            else:
                daily_report_df['first_in'] = pd.NaT
                daily_report_df['last_out'] = pd.NaT
                daily_report_df['hours'] = 0.0

            # Ghép dữ liệu nghỉ phép
            if not leave_df.empty:
                 daily_report_df = pd.merge(
                    daily_report_df,
                    leave_df[['emp_id', 'leave_date']],
                    left_on=['emp_id', 'date'],
                    right_on=['emp_id', 'leave_date'],
                    how='left'
                )
            else:
                daily_report_df['leave_date'] = pd.NaT

            # === 4. Áp dụng Logic Trạng thái ===
            daily_report_df['status'] = daily_report_df.apply(self._apply_status, axis=1)
            
            # Dọn dẹp: Gán 0 giờ cho ngày Vắng/Nghỉ phép
            daily_report_df.loc[daily_report_df['status'].isin(['Vắng', 'Nghỉ phép']), 'hours'] = 0.0
            
            # Định dạng lại các cột để hiển thị
            daily_report_df['hours'] = daily_report_df['hours'].fillna(0).round(2)
            daily_report_df['first_in'] = daily_report_df['first_in'].dt.strftime('%H:%M:%S').fillna('')
            daily_report_df['last_out'] = daily_report_df['last_out'].dt.strftime('%H:%M:%S').fillna('')
            daily_report_df['date'] = daily_report_df['date'].dt.strftime('%Y-%m-%d')
            
            # Chọn các cột cuối cùng cho Treeview
            self._daily_df = daily_report_df[[
                "emp_code", "name", "department", "date", 
                "status", "first_in", "last_out", "hours"
            ]]
            
            # === 5. Tạo Báo cáo Tổng hợp ===
            total_report = []
            for emp_id, group in daily_report_df.groupby('emp_id'):
                r = group.iloc[0]
                status_counts = group['status'].value_counts()
                
                total_report.append({
                    "emp_code": r['emp_code'],
                    "name": r['name'],
                    "department": r['department'],
                    "days_present": status_counts.get('Có mặt', 0) + status_counts.get('Đi muộn', 0),
                    "days_leave": status_counts.get('Nghỉ phép', 0),
                    "days_absent": status_counts.get('Vắng', 0),
                    "total_hours": group['hours'].sum().round(2)
                })
            
            self._total_df = pd.DataFrame.from_records(total_report)

            # === 6. Đổ dữ liệu lên UI ===
            self._populate_tree(self.tree_daily, self._daily_df)
            self._populate_tree(self.tree_total, self._total_df)
            
            messagebox.showinfo("Hoàn thành", "Đã tải báo cáo thành công!")

        except Exception as e:
            messagebox.showerror("Lỗi nghiêm trọng", f"Không thể tạo báo cáo: {e}")

    def export_daily_csv(self):
        if self._daily_df is None or self._daily_df.empty:
            messagebox.showwarning("Chú ý", "Không có dữ liệu chi tiết để xuất.")
            return
        
        fpath = filedialog.asksaveasfilename(
            defaultextension=".csv", 
            filetypes=[("CSV (UTF-8)", "*.csv")],
            initialfile=f"Bao_cao_chi_tiet_{self.start_var.get()}_den_{self.end_var.get()}.csv"
        )
        if not fpath:
            return
            
        try:
            self._daily_df.to_csv(fpath, index=False, encoding="utf-8-sig")
            messagebox.showinfo("OK", f"Đã lưu: {fpath}")
        except Exception as e:
             messagebox.showerror("Lỗi", f"Không thể lưu file: {e}")

    def export_total_csv(self):
        if self._total_df is None or self._total_df.empty:
            messagebox.showwarning("Chú ý", "Không có dữ liệu tổng hợp để xuất.")
            return
            
        fpath = filedialog.asksaveasfilename(
            defaultextension=".csv", 
            filetypes=[("CSV (UTF-8)", "*.csv")],
            initialfile=f"Bao_cao_tong_hop_{self.start_var.get()}_den_{self.end_var.get()}.csv"
        )
        if not fpath:
            return
            
        try:
            self._total_df.to_csv(fpath, index=False, encoding="utf-8-sig")
            messagebox.showinfo("OK", f"Đã lưu: {fpath}")
        except Exception as e:
             messagebox.showerror("Lỗi", f"Không thể lưu file: {e}")