import os

APP_TITLE = "Face Attendance - Desktop"
DATA_DIR = os.environ.get("FA_DATA_DIR", ".")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "face_attendance.db")

# lower = stricter
DEFAULT_TOL = 0.45
