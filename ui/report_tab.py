"""
Tab báo cáo chấm công - CÓ TÍNH CÔNG THEO GIỜ
"""

import datetime as dt
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import db
from config import DEFAULT_WORK_START_TIME, MIN_WORK_HOURS_FOR_FULL_DAY

class ReportTab(ttk.Frame):
    """Tab báo cáo chấm công"""
    def __init__(self, master):
        super().__init__(master)

        # ===== 1. Khung Lọc (Bên trên) =====
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Từ ngày:").pack(side="left", padx=(0, 5))
        self.start_var = tk.StringVar(value=str(dt.date.today().replace(day=1)))
        ttk.Entry(top, textvariable=self.start_var, width=12).pack(side="left", padx=5)

        ttk.Label(top, text="Đến ngày:").pack(side="left", padx=(10, 5))
        self.end_var = tk.StringVar(value=str(dt.date.today()))
        ttk.Entry(top, textvariable=self.end_var, width=12).pack(side="left", padx=5)

        ttk.Button(
            top, 
            text="📊 Lấy dữ liệu", 
            command=self.load_reports
        ).pack(side="left", padx=(15, 5))
        
        ttk.Button(
            top, 
            text="💾 Xuất CSV (Chi tiết)", 
            command=self.export_daily_csv
        ).pack(side="left", padx=5)
        
        ttk.Button(
            top, 
            text="💾 Xuất CSV (Tổng hợp)", 
            command=self.export_total_csv
        ).pack(side="left", padx=5)

        # ===== 2. Notebook cho 2 báo cáo =====
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Tab Chi tiết
        daily_frame = ttk.Frame(self.nb)
        self.nb.add(daily_frame, text="📅 Báo cáo chi tiết")

        # Thêm cột "Công" vào báo cáo chi tiết
        cols_daily = ("emp_code", "name", "department", "date", 
                      "status", "scans", "first_in", "last_out", "hours", "work_day")
        
        self.tree_daily = ttk.Treeview(daily_frame, columns=cols_daily, show="headings", height=20)
        
        self.tree_daily.heading("emp_code", text="Mã NV")
        self.tree_daily.heading("name", text="Họ tên")
        self.tree_daily.heading("department", text="Phòng ban")
        self.tree_daily.heading("date", text="Ngày")
        self.tree_daily.heading("status", text="Trạng thái")
        self.tree_daily.heading("scans", text="Số lần")
        self.tree_daily.heading("first_in", text="Giờ vào")
        self.tree_daily.heading("last_out", text="Giờ ra")
        self.tree_daily.heading("hours", text="Giờ làm")
        self.tree_daily.heading("work_day", text="Công")
        
        self.tree_daily.column("emp_code", width=80, anchor="center")
        self.tree_daily.column("name", width=150)
        self.tree_daily.column("department", width=120)
        self.tree_daily.column("date", width=100, anchor="center")
        self.tree_daily.column("status", width=120, anchor="center")
        self.tree_daily.column("scans", width=60, anchor="center")
        self.tree_daily.column("first_in", width=80, anchor="center")
        self.tree_daily.column("last_out", width=80, anchor="center")
        self.tree_daily.column("hours", width=70, anchor="center")
        self.tree_daily.column("work_day", width=60, anchor="center")
        
        self.tree_daily.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab Tổng hợp
        total_frame = ttk.Frame(self.nb)
        self.nb.add(total_frame, text="📊 Báo cáo tổng hợp")

        cols_total = ("emp_code", "name", "department", 
                      "total_work_days", "days_leave", "days_insufficient", "days_absent", "total_hours")
                      
        self.tree_total = ttk.Treeview(total_frame, columns=cols_total, show="headings", height=20)
        
        self.tree_total.heading("emp_code", text="Mã NV")
        self.tree_total.heading("name", text="Họ tên")
        self.tree_total.heading("department", text="Phòng ban")
        self.tree_total.heading("total_work_days", text="Ngày công")
        self.tree_total.heading("days_leave", text="Ngày phép")
        self.tree_total.heading("days_insufficient", text="Ngày thiếu giờ")
        self.tree_total.heading("days_absent", text="Ngày vắng")
        self.tree_total.heading("total_hours", text="Tổng giờ làm")
        
        self.tree_total.column("emp_code", width=90, anchor="center")
        self.tree_total.column("name", width=180)
        self.tree_total.column("department", width=130)
        self.tree_total.column("total_work_days", width=100, anchor="center")
        self.tree_total.column("days_leave", width=100, anchor="center")
        self.tree_total.column("days_insufficient", width=120, anchor="center")
        self.tree_total.column("days_absent", width=100, anchor="center")
        self.tree_total.column("total_hours", width=120, anchor="center")
        
        self.tree_total.pack(fill="both", expand=True, padx=5, pady=5)

        # Dữ liệu DataFrame
        self._daily_df = None
        self._total_df = None

    def parse_date(self, s: str):
        """Parse chuỗi ngày"""
        try:
            return dt.datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            return None

    def _populate_tree(self, tree: ttk.Treeview, df: pd.DataFrame):
        """Đổ dữ liệu vào Treeview"""
        for i in tree.get_children():
            tree.delete(i)
        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))

    def _apply_status(self, row):
        """Xác định trạng thái - CÓ KIỂM TRA SỐ GIỜ"""
        # Ưu tiên 1: Nghỉ phép
        if pd.notna(row['leave_date']):
            return "🏖️ Nghỉ phép"
        
        # Ưu tiên 2: Có giờ làm
        if pd.notna(row['hours']) and row['hours'] > 0:
            # Kiểm tra đủ giờ chưa
            if row['hours'] >= MIN_WORK_HOURS_FOR_FULL_DAY:
                # Đủ giờ, check đi muộn
                if pd.notna(row['first_in']) and row['first_in'].time() > DEFAULT_WORK_START_TIME:
                    return "⚠️ Đi muộn"
                return "✅ Đủ công"
            else:
                # Thiếu giờ
                return f"⚠️ Thiếu giờ ({row['hours']:.1f}h)"
        
        # Ưu tiên 3: Có IN nhưng thiếu OUT
        if pd.notna(row.get('scans')) and row['scans'] == 1:
            return "❌ Thiếu checkout"
        
        # Ưu tiên 4: Vắng
        return "❌ Vắng"

    def _calculate_work_day(self, row):
        """
        Tính ngày công:
        - Nghỉ phép: 0 công (hoặc có thể tính riêng)
        - Đủ giờ (>= MIN_WORK_HOURS): 1 công
        - Thiếu giờ/Vắng: 0 công
        """
        # Nghỉ phép
        if pd.notna(row['leave_date']):
            return 0  # Hoặc 'P' nếu muốn đánh dấu phép
        
        # Đủ giờ
        if pd.notna(row['hours']) and row['hours'] >= MIN_WORK_HOURS_FOR_FULL_DAY:
            return 1
        
        # Các trường hợp khác
        return 0

    def load_reports(self):
        """Tải và tổng hợp báo cáo - CÓ TÍNH CÔNG"""
        s = self.parse_date(self.start_var.get().strip())
        e = self.parse_date(self.end_var.get().strip())
        
        if s is None or e is None:
            messagebox.showwarning(
                "Sai định dạng", 
                "Ngày phải theo định dạng YYYY-MM-DD.\n\nVí dụ: 2024-01-01"
            )
            return
            
        if e < s:
            messagebox.showwarning("Lỗi", "Ngày kết thúc phải sau ngày bắt đầu.")
            return

        # Kiểm tra khoảng thời gian
        delta_days = (e - s).days
        if delta_days > 90:
            if not messagebox.askyesno(
                "Cảnh báo", 
                f"Bạn đang tải {delta_days} ngày dữ liệu.\n\n"
                f"Quá trình này có thể mất vài giây.\n\n"
                f"Tiếp tục?"
            ):
                return

        try:
            # === 1. Tải dữ liệu ===
            all_emps_df = db.get_all_employees()
            if all_emps_df.empty:
                messagebox.showinfo("Thông báo", "Không có nhân viên nào trong hệ thống.")
                return
            
            att_raw_df = db.get_attendance(s, e)
            work_hours_df = db.compute_work_hours(att_raw_df)
            
            leave_df = db.get_leave_records(s, e)
            if not leave_df.empty:
                leave_df['leave_date'] = pd.to_datetime(leave_df['leave_date'])
            
            # === 2. Tạo bảng đầy đủ ===
            all_days = pd.to_datetime(pd.date_range(s, e, freq='D'))
            
            base_df = all_emps_df[['id', 'emp_code', 'name', 'department']].copy()
            base_df['key'] = 1
            days_df = pd.DataFrame({'date': all_days, 'key': 1})
            
            daily_report_df = pd.merge(base_df, days_df, on='key').drop('key', axis=1)
            daily_report_df = daily_report_df.rename(columns={'id': 'emp_id'})

            # === 3. Ghép dữ liệu ===
            if not work_hours_df.empty:
                work_hours_df['date'] = pd.to_datetime(work_hours_df['date'])
                daily_report_df = pd.merge(
                    daily_report_df,
                    work_hours_df[['emp_id', 'date', 'first_in', 'last_out', 'scans', 'hours']],
                    on=['emp_id', 'date'],
                    how='left'
                )
            else:
                daily_report_df['first_in'] = pd.NaT
                daily_report_df['last_out'] = pd.NaT
                daily_report_df['scans'] = 0
                daily_report_df['hours'] = 0.0

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

            # === 4. Áp dụng Logic ===
            daily_report_df['status'] = daily_report_df.apply(self._apply_status, axis=1)
            daily_report_df['work_day'] = daily_report_df.apply(self._calculate_work_day, axis=1)
            
            daily_report_df['hours'] = daily_report_df['hours'].fillna(0).round(2)
            daily_report_df['scans'] = daily_report_df['scans'].fillna(0).astype(int)
            daily_report_df['first_in'] = daily_report_df['first_in'].dt.strftime('%H:%M:%S').fillna('')
            daily_report_df['last_out'] = daily_report_df['last_out'].dt.strftime('%H:%M:%S').fillna('')
            daily_report_df['date'] = daily_report_df['date'].dt.strftime('%Y-%m-%d')
            
            self._daily_df = daily_report_df[[
                "emp_code", "name", "department", "date", 
                "status", "scans", "first_in", "last_out", "hours", "work_day"
            ]].sort_values(['date', 'emp_code'], ascending=[False, True])
            
            # === 5. Báo cáo Tổng hợp ===
            total_report = []
            for emp_id, group in daily_report_df.groupby('emp_id'):
                r = group.iloc[0]
                status_counts = group['status'].value_counts()
                
                # Đếm các loại ngày
                days_leave = status_counts.get('🏖️ Nghỉ phép', 0)
                days_absent = status_counts.get('❌ Vắng', 0) + status_counts.get('❌ Thiếu checkout', 0)
                
                # Đếm ngày thiếu giờ (bắt đầu bằng "⚠️ Thiếu giờ")
                days_insufficient = sum(1 for status in group['status'] if '⚠️ Thiếu giờ' in status)
                
                # Tổng ngày công (work_day = 1)
                total_work_days = group['work_day'].sum()
                
                total_report.append({
                    "emp_code": r['emp_code'],
                    "name": r['name'],
                    "department": r['department'],
                    "total_work_days": total_work_days,
                    "days_leave": days_leave,
                    "days_insufficient": days_insufficient,
                    "days_absent": days_absent,
                    "total_hours": group['hours'].sum().round(2)
                })
            
            self._total_df = pd.DataFrame.from_records(total_report).sort_values('emp_code')

            # === 6. Hiển thị ===
            self._populate_tree(self.tree_daily, self._daily_df)
            self._populate_tree(self.tree_total, self._total_df)
            
            messagebox.showinfo(
                "Hoàn thành", 
                f"Đã tải báo cáo thành công!\n\n"
                f"Số bản ghi: {len(self._daily_df)}\n"
                f"Số nhân viên: {len(self._total_df)}\n\n"
                f"⚠️ Quy định: Tối thiểu {MIN_WORK_HOURS_FOR_FULL_DAY}h mới tính công"
            )

        except Exception as e:
            messagebox.showerror("Lỗi nghiêm trọng", f"Không thể tạo báo cáo:\n\n{e}")
            import traceback
            traceback.print_exc()

    def export_daily_csv(self):
        """Xuất báo cáo chi tiết"""
        if self._daily_df is None or self._daily_df.empty:
            messagebox.showwarning("Chú ý", "Chưa có dữ liệu. Vui lòng tải báo cáo trước.")
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
            messagebox.showinfo("Thành công", f"Đã lưu file:\n{fpath}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu file: {e}")

    def export_total_csv(self):
        """Xuất báo cáo tổng hợp"""
        if self._total_df is None or self._total_df.empty:
            messagebox.showwarning("Chú ý", "Chưa có dữ liệu. Vui lòng tải báo cáo trước.")
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
            messagebox.showinfo("Thành công", f"Đã lưu file:\n{fpath}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu file: {e}")