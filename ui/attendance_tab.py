
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from config import DEFAULT_TOL
from services import db
from services.face import face_encode_from_image, match_employee

try:
    import cv2
except Exception:
    cv2 = None


class AttendanceTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        # Controls
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Ngưỡng nhận diện (nhỏ = chặt):").pack(side="left")
        self.scale_tol = ttk.Scale(top, from_=0.30, to=0.70, value=DEFAULT_TOL,
                                   orient="horizontal", length=200)
        self.scale_tol.pack(side="left", padx=6)

        ttk.Button(top, text="Bật camera", command=self.start_camera).pack(side="left", padx=4)
        ttk.Button(top, text="Tắt camera", command=self.stop_camera).pack(side="left", padx=4)
        ttk.Button(top, text="Chấm công (chụp)", command=self.scan_and_mark).pack(side="left", padx=4)

        # Video panel
        self.video_panel = ttk.Label(self, relief="sunken", anchor="center")
        self.video_panel.pack(fill="both", expand=True, padx=10, pady=10)

        self.att_status = tk.StringVar(value="Chưa có thao tác.")
        ttk.Label(self, textvariable=self.att_status).pack(pady=6)

        # Webcam state
        self.cap = None
        self._updating = False         # dùng after-loop thay vì thread
        self._frame_imgtk = None       # giữ tham chiếu ảnh để không bị GC
        self._target_w, self._target_h = 900, 520
        self._interval_ms = 33         # ~30 FPS

    # ---------- Camera ----------
    def start_camera(self):
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

        # Gợi ý tham số để mượt hơn (nhiều thiết bị sẽ tôn trọng)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # giảm độ trễ

        self._updating = True
        self._update_video_after()
        self.att_status.set("Camera đã bật.")

    def stop_camera(self):
        self._updating = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        # Xoá ảnh khi tắt hẳn để tránh nháy
        self.video_panel.configure(image="")
        self._frame_imgtk = None
        self.att_status.set("Camera đã tắt.")

    def _update_video_after(self):
        """Cập nhật khung hình bằng Tk.after (main thread) để tránh giật/chớp."""
        if not self._updating or self.cap is None:
            return

        # Đọc frame; nếu backend tích buffer, gọi grab() để bỏ bớt frame cũ
        # (không phải backend nào cũng cần, nhưng thường giúp giảm trễ)
        _ = self.cap.grab()
        ret, frame = self.cap.read()
        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            # Giữ tỉ lệ ảnh, scale vừa panel -> ít hao CPU hơn so với resize cứng
            img.thumbnail((self._target_w, self._target_h), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self._frame_imgtk = imgtk
            self.video_panel.configure(image=imgtk)

        # Lặp lại ~30fps
        self.after(self._interval_ms, self._update_video_after)

    def scan_and_mark(self):
        tol = float(self.scale_tol.get())
        if self.cap is None:
            messagebox.showwarning("Chú ý", "Hãy bật camera trước.")
            return

        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Lỗi", "Không đọc được frame từ camera.")
            return

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        try:
            enc = face_encode_from_image(img)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xử lý ảnh: {e}")
            return

        if enc is None:
            self.att_status.set("Không phát hiện được khuôn mặt. Thử lại.")
            return

        m = match_employee(enc, tol)
        if m is None:
            self.att_status.set("❌ Không khớp với nhân viên nào (Unknown). Vào tab Nhân viên để thêm.")
        else:
            db.mark_attendance(int(m["id"]))
            self.att_status.set(f"✅ Đã chấm công cho {m['name']} (khoảng cách={m['distance']:.3f}).")

    # ---------- Lifecycle ----------
    def on_close(self):
        self._updating = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
