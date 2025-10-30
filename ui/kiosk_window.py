# -*- coding: utf-8 -*-
"""
Cửa sổ Kiosk Chấm công - Giao diện đơn giản, Logic đầy đủ
ĐÃ CẬP NHẬT: Giới hạn 2 lần chấm công/ngày (1 VÀO + 1 RA)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime as dt
from PIL import Image, ImageTk

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import APP_TITLE, DEFAULT_TOL
from services import db
from services.face import face_encode_from_image, match_employee

try:
    import cv2
except Exception:
    cv2 = None


class KioskWindow(tk.Tk):
    """Cửa sổ Kiosk Chấm công - Giao diện đơn giản, Logic đầy đủ"""
    
    def __init__(self):
        super().__init__()
        
        # === CẤU HÌNH CỬA SỔ ===
        self.title(f"{APP_TITLE} - Kiosk Chấm Công")
        self.geometry("950x650")
        self.resizable(False, False)
        
        # Căn giữa màn hình
        self._center_window()
        
        # === TRẠNG THÁI ===
        self.cap = None
        self._updating = False
        self._is_scanning = False
        self._frame_imgtk = None
        self._target_w, self._target_h = 900, 520
        self._interval_ms = 33
        
        # Logic chấm công
        self._cooldown_seconds = 10
        self._last_scan_emp_id = None
        self._last_scan_time = None
        
        # === XÂY DỰNG GIAO DIỆN ===
        self._build_ui()
        
        # === SỰ KIỆN ===
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _center_window(self):
        """Căn giữa cửa sổ"""
        self.update_idletasks()
        width = 950
        height = 650
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _build_ui(self):
        """Xây dựng giao diện"""
        
        # === CONTROLS ===
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Ngưỡng nhận diện (nhỏ = chặt):").pack(side="left")
        self.scale_tol = ttk.Scale(top, from_=0.30, to=0.70, value=DEFAULT_TOL,
                                   orient="horizontal", length=200)
        self.scale_tol.pack(side="left", padx=6)

        ttk.Button(top, text="Bật camera", command=self.start_camera).pack(side="left", padx=4)
        ttk.Button(top, text="Tắt camera", command=self.stop_camera).pack(side="left", padx=4)
        ttk.Button(top, text="Chấm công (chụp)", command=self.on_scan_button_click).pack(side="left", padx=4)

        # === VIDEO PANEL ===
        self.video_panel = ttk.Label(self, relief="sunken", anchor="center")
        self.video_panel.pack(fill="both", expand=True, padx=10, pady=10)

        # === STATUS ===
        self.att_status = tk.StringVar(value="Chưa có thao tác.")
        ttk.Label(self, textvariable=self.att_status, wraplength=900, justify="center").pack(pady=6)

    # ==================== CAMERA ====================
    
    def start_camera(self):
        """Khởi động camera"""
        if cv2 is None:
            messagebox.showerror("Lỗi", "OpenCV (cv2) chưa được cài đặt.")
            return
        if self.cap is not None:
            return

        # Mở camera (CAP_DSHOW giúp ổn định trên Windows)
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        except Exception:
            self.cap = cv2.VideoCapture(0)

        if not self.cap or not self.cap.isOpened():
            self.cap = None
            messagebox.showerror("Lỗi", "Không mở được webcam.")
            return

        # Gợi ý tham số để mượt hơn
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self._updating = True
        self._update_video_after()
        self.att_status.set("Camera đã bật.")

    def stop_camera(self):
        """Dừng camera"""
        self._updating = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        # Xoá ảnh khi tắt
        self.video_panel.configure(image="")
        self._frame_imgtk = None
        self.att_status.set("Camera đã tắt.")

    def _update_video_after(self):
        """Cập nhật khung hình bằng Tk.after (main thread) để tránh giật/chớp."""
        if not self._updating or self.cap is None:
            return

        # Đọc frame
        _ = self.cap.grab()
        ret, frame = self.cap.read()
        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            # Giữ tỉ lệ ảnh, scale vừa panel
            img.thumbnail((self._target_w, self._target_h), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self._frame_imgtk = imgtk
            self.video_panel.configure(image=imgtk)

        # Lặp lại ~30fps
        self.after(self._interval_ms, self._update_video_after)

    # ==================== CHẤM CÔNG ====================
    
    def on_scan_button_click(self):
        """Xử lý khi nhấn nút CHẤM CÔNG"""
        if self._is_scanning:
            self.att_status.set("⏳ Đang xử lý, vui lòng đợi...")
            return
        
        if self.cap is None:
            messagebox.showwarning("Chú ý", "Hãy bật camera trước.")
            return
        
        self._is_scanning = True
        
        # Đếm ngược
        self.att_status.set("📸 Chuẩn bị: 3...")
        self.after(700, lambda: self._countdown(2))
    
    def _countdown(self, count):
        """Đếm ngược"""
        if count > 0:
            self.att_status.set(f"📸 Chuẩn bị: {count}...")
            self.after(700, lambda: self._countdown(count - 1))
        else:
            self.att_status.set("📸 CHỤP! Đang nhận diện...")
            self.after(200, self._perform_scan)
    
    def _perform_scan(self):
        """Thực hiện quét và nhận diện - ĐÃ CẬP NHẬT LOGIC"""
        tol = float(self.scale_tol.get())
        
        # Đọc frame
        ret, frame = self.cap.read()
        if not ret:
            self._finish_scan("❌ Lỗi: Không đọc được ảnh từ camera.")
            return
        
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Encode khuôn mặt
        self.att_status.set("🔍 Đang phân tích khuôn mặt...")
        self.update()
        
        try:
            enc = face_encode_from_image(img)
        except Exception as e:
            self._finish_scan(f"❌ Lỗi xử lý ảnh: {e}")
            return
        
        if enc is None:
            self._finish_scan(
                "❌ KHÔNG PHÁT HIỆN KHUÔN MẶT | "
                "Vui lòng: Đứng gần camera hơn, Nhìn thẳng vào camera, Đảm bảo đủ ánh sáng"
            )
            return
        
        # Tìm kiếm nhân viên
        self.att_status.set("🔎 Đang tìm kiếm nhân viên...")
        self.update()
        
        m = match_employee(enc, tol)
        if m is None:
            self._finish_scan(
                "❌ KHÔNG NHẬN DIỆN ĐƯỢC | "
                "Khuôn mặt không có trong hệ thống. Vui lòng liên hệ quản trị viên."
            )
            return
        
        # Thông tin nhân viên
        emp_id = int(m["id"])
        emp_name = m["name"]
        emp_code = m.get("emp_code", "N/A")
        distance = m.get("distance", 0)
        now = dt.datetime.now()
        
        # Kiểm tra Cooldown
        if (self._last_scan_emp_id == emp_id and
            self._last_scan_time is not None and
            (now - self._last_scan_time).total_seconds() < self._cooldown_seconds):
            
            remaining = self._cooldown_seconds - int(
                (now - self._last_scan_time).total_seconds()
            )
            self._finish_scan(
                f"⏱️ BẠN ĐÃ CHẤM CÔNG GẦN ĐÂY | "
                f"Vui lòng đợi {remaining} giây nữa."
            )
            return
        
        # Kiểm tra Nghỉ phép
        try:
            if hasattr(db, 'is_employee_on_leave') and db.is_employee_on_leave(emp_id, now.date()):
                self._finish_scan(
                    f"🏖️ NGHỈ PHÉP | "
                    f"{emp_name} ({emp_code}) đang trong kỳ nghỉ phép. Không thể chấm công."
                )
                self._last_scan_emp_id = emp_id
                self._last_scan_time = now
                return
        except Exception:
            pass
        
        # ===== GHI NHẬN CHẤM CÔNG - LOGIC MỚI =====
        self.att_status.set("💾 Đang lưu dữ liệu...")
        self.update()
        
        try:
            result = db.mark_attendance(emp_id)
            
            # Xử lý kết quả trả về (hỗ trợ cả tuple và giá trị đơn)
            if isinstance(result, tuple):
                if len(result) >= 3:
                    # Định dạng mới: (ok, msg, scan_type)
                    ok, msg, scan_type = result
                elif len(result) >= 2:
                    # Định dạng không có scan_type
                    ok, msg = result
                    scan_type = 'IN'
                else:
                    ok = result[0]
                    msg = 'Thành công'
                    scan_type = 'IN'
            else:
                # Định dạng cũ: chỉ trả về boolean
                ok = bool(result)
                msg = 'Chấm công thành công'
                scan_type = 'IN'
            
            if ok:
                # ===== CHẤM CÔNG THÀNH CÔNG =====
                icon = "🟢" if scan_type == 'IN' else "🔴"
                action = "VÀO LÀM" if scan_type == 'IN' else "TAN LÀM"
                
                self._finish_scan(
                    f"{icon} CHẤM CÔNG THÀNH CÔNG! | "
                    f"👤 {emp_name} | 🆔 {emp_code} | "
                    f"📏 Khoảng cách: {distance:.3f} | "
                    f"⏰ {now.strftime('%H:%M:%S - %d/%m/%Y')} | "
                    f"📍 {action} | "
                    f"{msg}"
                )
                self._last_scan_emp_id = emp_id
                self._last_scan_time = now
                
            else:
                # ===== BỊ TỪ CHỐI =====
                # Kiểm tra loại lỗi
                msg_upper = msg.upper()
                
                if any(keyword in msg_upper for keyword in ["ĐÃ ĐỦ", "CHẶN", "BẤT THƯỜNG", "2 LẦN"]):
                    # Lỗi nghiệp vụ: Đã đủ 2 lần chấm công
                    self._finish_scan(
                        f"⛔ {emp_name} ({emp_code}) | {msg}"
                    )
                    # Vẫn set cooldown để tránh spam
                    self._last_scan_emp_id = emp_id
                    self._last_scan_time = now
                else:
                    # Lỗi hệ thống khác
                    self._finish_scan(f"❌ Lỗi: {msg}")
                    
        except Exception as e:
            # Lỗi exception
            import traceback
            traceback.print_exc()
            self._finish_scan(f"❌ Lỗi hệ thống: {e}")
    
    def _finish_scan(self, message: str):
        """Kết thúc quá trình quét"""
        self._is_scanning = False
        self.att_status.set(message)

    # ==================== LIFECYCLE ====================
    
    def on_close(self):
        """Đóng cửa sổ"""
        self._updating = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.destroy()


# ==================== MAIN ====================

if __name__ == "__main__":
    app = KioskWindow()
    app.mainloop()