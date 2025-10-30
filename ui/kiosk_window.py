# Tên file: ui/kiosk_window.py

import tkinter as tk
from tkinter import ttk, messagebox
import datetime as dt
from PIL import Image, ImageTk

from config import APP_TITLE, DEFAULT_TOL
from services import db
from services.face import face_encode_from_image, match_employee

try:
    import cv2
except Exception:
    cv2 = None

class KioskWindow(tk.Tk):
    """
    Cửa sổ chính cho Ứng dụng Kiosk Chấm công (chỉ Camera).
    Kế thừa từ file attendance_tab.py cũ.
    """
    def __init__(self):
        super().__init__()

        # === Cấu hình cửa sổ ===
        self.title(f"{APP_TITLE} - Kiosk")
        # Chạy toàn màn hình
        self.attributes('-fullscreen', True)
        self.configure(bg="#e8f0fe")
        
        # Style (chỉ dùng cho Label)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#e8f0fe")
        style.configure("TLabel", background="#e8f0fe", font=("Segoe UI", 10))

        # === Giao diện ===
        # 1. Bảng Video
        self.video_panel = ttk.Label(self, relief="sunken", anchor="center")
        self.video_panel.pack(fill="both", expand=True, padx=20, pady=20)

        # 2. Trạng thái
        self.att_status = tk.StringVar(value="Đang khởi động camera...")
        status_label = ttk.Label(
            self, 
            textvariable=self.att_status,
            font=("Segoe UI", 14, "bold"),
            anchor="center"
        )
        status_label.pack(fill="x", pady=10)

        # === Trạng thái Webcam ===
        self.cap = None
        self._updating_video = False # Cờ cho vòng lặp update video
        self._auto_scanning = False  # Cờ cho vòng lặp auto-scan
        self._frame_imgtk = None
        self._target_w, self._target_h = 1280, 720
        self._video_interval_ms = 33 # ~30 FPS cho video
        self._scan_interval_ms = 2000  # Quét 2 giây / lần
        
        # === Trạng thái Cooldown ===
        self._last_scan_emp_id = None
        self._last_scan_time = None
        self._cooldown_seconds = 10 # Chờ 10s trước khi quét lại cùng 1 người

        # === Sự kiện ===
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # Bắt phím 'q' hoặc 'Esc' để thoát toàn màn hình
        self.bind("<Escape>", self._exit_fullscreen)
        self.bind("q", self._exit_fullscreen)
        
        # Tự động khởi động
        self.after(100, self.start_camera)

    def _exit_fullscreen(self, event=None):
        """Cho phép thoát fullscreen bằng phím Esc hoặc Q"""
        self.attributes('-fullscreen', False)
        self.geometry("1024x768")

    # ---------- Camera ----------
    def start_camera(self):
        if cv2 is None:
            messagebox.showerror("Lỗi", "OpenCV (cv2) chưa được cài đặt.")
            self.on_close()
            return
        if self.cap is not None:
            return

        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        except Exception:
            self.cap = cv2.VideoCapture(0)

        if not self.cap or not self.cap.isOpened():
            self.cap = None
            messagebox.showerror("Lỗi", "Không mở được webcam.")
            self.on_close()
            return

        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Bắt đầu cả 2 vòng lặp: 1 cho video, 1 cho scan
        self._updating_video = True
        self._auto_scanning = True
        
        self._update_video_after() # Bắt đầu vòng lặp video (nhanh)
        self.after(self._scan_interval_ms, self._auto_scan) # Bắt đầu vòng lặp scan (chậm)
        
        self.att_status.set("Camera đã bật. Sẵn sàng chấm công.")

    def stop_camera(self):
        # Dừng cả 2 vòng lặp
        self._updating_video = False
        self._auto_scanning = False
        
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
            
        self.video_panel.configure(image="")
        self._frame_imgtk = None
        self.att_status.set("Camera đã tắt.")

    def _update_video_after(self):
        """Vòng lặp 1: Cập nhật khung hình (nhanh ~30 FPS)"""
        if not self._updating_video or self.cap is None:
            return

        _ = self.cap.grab()
        ret, frame = self.cap.read()
        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img.thumbnail((self._target_w, self._target_h), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self._frame_imgtk = imgtk
            self.video_panel.configure(image=imgtk)

        self.after(self._video_interval_ms, self._update_video_after)

    def _auto_scan(self):
        """Vòng lặp 2: Tự động quét (chậm, mỗi 2 giây)"""
        if not self._auto_scanning or self.cap is None:
            return

        # Thực hiện quét
        try:
            self.scan_and_mark()
        except Exception as e:
            print(f"Lỗi khi auto-scan: {e}")
            self.att_status.set(f"Lỗi xử lý: {e}")
            
        # Lên lịch quét tiếp theo
        self.after(self._scan_interval_ms, self._auto_scan)

    def scan_and_mark(self):
        """Thực hiện quét, nhận diện và chấm công (đã sửa đổi)"""
        tol = DEFAULT_TOL # Lấy từ config
        if self.cap is None:
            # Camera chưa sẵn sàng, bỏ qua lần quét này
            return

        ret, frame = self.cap.read()
        if not ret:
            self.att_status.set("Lỗi: Không đọc được frame.")
            return

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        try:
            enc = face_encode_from_image(img)
        except Exception as e:
            self.att_status.set(f"Lỗi xử lý ảnh: {e}")
            return

        if enc is None:
            self.att_status.set("Không phát hiện được khuôn mặt. Vui lòng nhìn thẳng.")
            return

        m = match_employee(enc, tol)
        if m is None:
            self.att_status.set("❌ Không khớp với nhân viên nào (Unknown).")
            return

        # === Logic mới: Cooldown & Nghỉ phép ===
        emp_id = int(m["id"])
        emp_name = m["name"]
        now = dt.datetime.now()

        # 1. Kiểm tra Cooldown: Tránh quét 1 người liên tục
        if (self._last_scan_emp_id == emp_id and
            self._last_scan_time is not None and
            (now - self._last_scan_time).total_seconds() < self._cooldown_seconds):
            
            self.att_status.set(f"Đã quét {emp_name}. Vui lòng đợi {self._cooldown_seconds}s.")
            return

        # 2. Kiểm tra Nghỉ phép:
        try:
            if db.is_employee_on_leave(emp_id, now.date()):
                self.att_status.set(f"❌ {emp_name} đang trong kỳ nghỉ phép. Không thể chấm công.")
                self._last_scan_emp_id = emp_id
                self._last_scan_time = now
                return
        except Exception as e:
            self.att_status.set(f"Lỗi kiểm tra nghỉ phép: {e}")
            return

        # 3. Ghi nhận chấm công (Gọi hàm IN/OUT mới)
        try:
            ok, msg, scan_type = db.mark_attendance(emp_id)
            if ok:
                # Chấm công thành công, cập nhật trạng thái
                self.att_status.set(f"{msg} ({emp_name})")
                self._last_scan_emp_id = emp_id
                self._last_scan_time = now
            else:
                self.att_status.set(msg)
        except Exception as e:
            self.att_status.set(f"Lỗi ghi CSDL: {e}")

    # ---------- Lifecycle ----------
    def on_close(self):
        """Tắt camera và hủy cửa sổ"""
        self.stop_camera()
        self.destroy()