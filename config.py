"""
File cấu hình hệ thống
Chỉnh sửa file này để thay đổi cấu hình kết nối database
"""

import os

# ============================================================================
# CẤU HÌNH ỨNG DỤNG
# ============================================================================
APP_TITLE = "Face Attendance - Desktop"
APP_VERSION = "2.0.0"

# ============================================================================
# CẤU HÌNH DATABASE MYSQL
# ============================================================================
# 🔧 THAY ĐỔI CẤU HÌNH TẠI ĐÂY
DB_CONFIG = {
    "host": "localhost",           # IP máy chủ MySQL (localhost nếu cùng máy)
    "port": 3306,                  # Port MySQL (mặc định 3306)
    "user": "root",                # Username MySQL
    "password": "duc123",          # Password MySQL
    "database": "face_attendance", # Tên database
    "charset": "utf8mb4",
    "use_unicode": True,
    "autocommit": False,
    "pool_size": 5,                # Số lượng connection trong pool
    "pool_reset_session": True,
}

# ============================================================================
# CẤU HÌNH NHẬN DIỆN KHUÔN MẶT
# ============================================================================
# Ngưỡng nhận diện (0.0 - 1.0)
# Càng thấp = càng chặt chẽ (0.4 - 0.6 là tốt nhất)
DEFAULT_TOL = 0.45

# Model nhận diện khuôn mặt
# "hog" = nhanh hơn, dùng CPU
# "cnn" = chính xác hơn, cần GPU
FACE_DETECTION_MODEL = "hog"

# ============================================================================
# CẤU HÌNH KIOSK
# ============================================================================
# Thời gian cooldown giữa 2 lần quét (giây)
KIOSK_COOLDOWN_SECONDS = 10

# Khoảng thời gian tự động quét (milliseconds)
KIOSK_SCAN_INTERVAL_MS = 2000

# FPS camera
KIOSK_VIDEO_FPS = 30

# ============================================================================
# CẤU HÌNH CHẤM CÔNG
# ============================================================================
# Giờ làm việc tiêu chuẩn
DEFAULT_WORK_START_TIME = "08:30:00"
DEFAULT_WORK_END_TIME = "17:30:00"

# ============================================================================
# CẤU HÌNH THƯ MỤC LƯU TRỮ
# ============================================================================
DATA_DIR = os.environ.get("FA_DATA_DIR", ".")
os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================================
# LOGGING
# ============================================================================
ENABLE_DEBUG_LOG = False