# services/db.py
"""
Module xử lý Database cho Hệ thống Chấm công Nhận diện Khuôn mặt

"""

import io
import datetime as dt
from typing import Optional, Tuple, List, Dict

import numpy as np
import pandas as pd
import bcrypt

import mysql.connector
from mysql.connector import Error

# ============================================================================
# CẤU HÌNH MYSQL
# ============================================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "duc123",
    "database": "face_attendance",
    "charset": "utf8mb4",
    "use_unicode": True,
}

# ============================================================================
# KẾT NỐI DATABASE
# ============================================================================

def get_conn():
    """Tạo kết nối MySQL"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        raise RuntimeError(f"❌ Lỗi kết nối MySQL: {e}")


# ============================================================================
# KHỞI TẠO DATABASE
# ============================================================================

def init_db():
    """
    Khởi tạo database lần đầu
    Chỉ INSERT tài khoản admin mặc định với password đã hash
    """
    con = get_conn()
    try:
        cur = con.cursor()
        
        cur.execute("SELECT COUNT(*) FROM users WHERE username=%s", ("admin",))
        count = cur.fetchone()[0]
        
        if count == 0:
            default_password = "admin123"
            hashed = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())
            
            cur.execute(
                "INSERT INTO users(username, password) VALUES(%s, %s)",
                ("admin", hashed.decode('utf-8'))
            )
            con.commit()
            print("✅ Đã tạo tài khoản admin mặc định (admin/admin123)")
        
    finally:
        try:
            cur.close()
        except Exception:
            pass
        con.close()


# ============================================================================
# XÁC THỰC
# ============================================================================

def check_login(username: str, password: str) -> bool:
    """Kiểm tra đăng nhập admin với bcrypt"""
    con = get_conn()
    cur = con.cursor()
    try:
        cur.execute(
            "SELECT password FROM users WHERE username=%s LIMIT 1",
            (username,)
        )
        result = cur.fetchone()
        
        if result is None:
            return False
        
        stored_hash = result[0]
        
        # Password cũ chưa hash (plain text) - tự động upgrade
        if not stored_hash.startswith('$2b$'):
            if password == stored_hash:
                new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cur.execute(
                    "UPDATE users SET password=%s WHERE username=%s",
                    (new_hash.decode('utf-8'), username)
                )
                con.commit()
                return True
            return False
        
        # Verify password với bcrypt
        return bcrypt.checkpw(
            password.encode('utf-8'),
            stored_hash.encode('utf-8')
        )
        
    except Exception as e:
        print(f"❌ Lỗi check_login: {e}")
        return False
    finally:
        try:
            cur.close()
        finally:
            con.close()


# ============================================================================
# NUMPY <-> BLOB
# ============================================================================

def np_to_blob(vec: np.ndarray) -> bytes:
    """Chuyển numpy array thành blob để lưu MySQL"""
    buf = io.BytesIO()
    np.save(buf, vec.astype(np.float32))
    return buf.getvalue()


def blob_to_np(blob: bytes) -> np.ndarray:
    """Chuyển blob từ MySQL thành numpy array"""
    buf = io.BytesIO(blob)
    buf.seek(0)
    return np.load(buf, allow_pickle=False)


# ============================================================================
# QUẢN LÝ NHÂN VIÊN
# ============================================================================

def load_all_embeddings() -> pd.DataFrame:
    """Load tất cả nhân viên kèm embedding vector"""
    con = get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT id, emp_code, name, department, phone, embedding FROM employees",
            con,
        )
    finally:
        con.close()

    if not df.empty:
        df["embedding_vec"] = df["embedding"].apply(blob_to_np)
    else:
        df["embedding_vec"] = []
    return df


def add_employee(emp_code: str, name: str, department: str, 
                phone: str, embedding: np.ndarray) -> Tuple[bool, str]:
    """Thêm nhân viên mới"""
    con = get_conn()
    cur = con.cursor()
    try:
        cur.execute("""
            INSERT INTO employees(emp_code, name, department, phone, embedding, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (emp_code, name, department, phone, np_to_blob(embedding), dt.datetime.now()))
        con.commit()
        return True, "✅ Đã thêm nhân viên."
    except mysql.connector.IntegrityError:
        return False, "❌ Mã nhân viên đã tồn tại."
    except Exception as e:
        return False, f"❌ Lỗi: {e}"
    finally:
        try:
            cur.close()
        finally:
            con.close()


def delete_employee(emp_id: int) -> None:
    """Xóa nhân viên"""
    con = get_conn()
    cur = con.cursor()
    try:
        cur.execute("DELETE FROM employees WHERE id=%s", (emp_id,))
        con.commit()
    finally:
        try:
            cur.close()
        finally:
            con.close()


def get_all_employees() -> pd.DataFrame:
    """Lấy danh sách nhân viên (không có embedding)"""
    con = get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT id, emp_code, name, department, phone, created_at FROM employees ORDER BY emp_code",
            con
        )
    finally:
        con.close()
    return df


# ============================================================================
# CHẤM CÔNG - LOGIC IN/OUT
# ============================================================================

def get_last_scan_today(emp_id: int) -> Optional[Dict]:
    """Lấy lần quét cuối cùng hôm nay"""
    con = get_conn()
    cur = con.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT scan_type, ts
            FROM attendance
            WHERE emp_id = %s AND DATE(ts) = CURDATE()
            ORDER BY ts DESC
            LIMIT 1
        """, (emp_id,))
        
        return cur.fetchone()
        
    finally:
        try:
            cur.close()
        finally:
            con.close()


def determine_scan_type(emp_id: int) -> str:
    """
    Xác định scan_type tiếp theo (IN hoặc OUT)
    - Chưa quét -> IN
    - Lần cuối IN -> OUT
    - Lần cuối OUT -> IN
    """
    last_scan = get_last_scan_today(emp_id)
    
    if last_scan is None:
        return 'IN'
    
    return 'OUT' if last_scan['scan_type'] == 'IN' else 'IN'


def mark_attendance(emp_id: int, device: str = "KIOSK-01") -> Tuple[bool, str, str]:
    """Ghi nhận chấm công tự động IN/OUT"""
    con = get_conn()
    cur = con.cursor()
    try:
        scan_type = determine_scan_type(emp_id)
        
        cur.execute("""
            INSERT INTO attendance(emp_id, ts, device, scan_type)
            VALUES (%s, %s, %s, %s)
        """, (emp_id, dt.datetime.now(), device, scan_type))
        con.commit()
        
        action = "VÀO" if scan_type == 'IN' else "RA"
        return True, f"✅ Chấm công {action} thành công!", scan_type
        
    except Exception as e:
        return False, f"❌ Lỗi ghi chấm công: {e}", ""
    finally:
        try:
            cur.close()
        finally:
            con.close()


def get_attendance(start: Optional[dt.date] = None, 
                  end: Optional[dt.date] = None) -> pd.DataFrame:
    """Lấy lịch sử chấm công trong khoảng thời gian"""
    con = get_conn()
    try:
        q = """
            SELECT
                a.emp_id,
                e.emp_code,
                e.name,
                e.department,
                a.ts,
                a.device,
                a.scan_type
            FROM attendance a
            JOIN employees e ON e.id = a.emp_id
        """
        params = []
        where = []
        
        if start and end:
            where.append("DATE(a.ts) BETWEEN %s AND %s")
            params += [start, end]
        elif start:
            where.append("DATE(a.ts) >= %s")
            params.append(start)
        elif end:
            where.append("DATE(a.ts) <= %s")
            params.append(end)

        if where:
            q += " WHERE " + " AND ".join(where)
        q += " ORDER BY a.ts DESC"

        df = pd.read_sql_query(q, con, params=params)
    finally:
        con.close()

    if not df.empty:
        df["ts"] = pd.to_datetime(df["ts"])
    return df


def compute_work_hours(att_df: pd.DataFrame) -> pd.DataFrame:
    """Tính giờ làm việc dựa trên các cặp IN-OUT"""
    if att_df.empty:
        return pd.DataFrame(columns=[
            'emp_id', 'name', 'department', 'date', 
            'first_in', 'last_out', 'scans', 'hours'
        ])
    
    df = att_df.copy()
    df["date"] = df["ts"].dt.date
    
    df_in = df[df['scan_type'] == 'IN'].copy()
    df_out = df[df['scan_type'] == 'OUT'].copy()
    
    group_cols = ["emp_id", "name", "department", "date"]
    
    first_in = (
        df_in.groupby(group_cols)['ts']
        .min()
        .reset_index()
        .rename(columns={'ts': 'first_in'})
    )
    
    last_out = (
        df_out.groupby(group_cols)['ts']
        .max()
        .reset_index()
        .rename(columns={'ts': 'last_out'})
    )
    
    scans = (
        df.groupby(group_cols)['ts']
        .count()
        .reset_index()
        .rename(columns={'ts': 'scans'})
    )
    
    agg = first_in.merge(last_out, on=group_cols, how='outer')
    agg = agg.merge(scans, on=group_cols, how='left')
    
    agg['hours'] = 0.0
    
    mask = agg['first_in'].notna() & agg['last_out'].notna()
    agg.loc[mask, 'hours'] = (
        (agg.loc[mask, 'last_out'] - agg.loc[mask, 'first_in'])
        .dt.total_seconds() / 3600.0
    )
    
    agg.loc[agg['scans'] <= 1, 'hours'] = 0.0
    agg['hours'] = agg['hours'].round(2)
    
    return agg.sort_values(['date', 'emp_id'], ascending=[False, True])


# ============================================================================
# QUẢN LÝ NGHỈ PHÉP
# ============================================================================

def add_leave(emp_id: int, leave_date: dt.date, 
             reason: str = "Nghỉ phép") -> Tuple[bool, str]:
    """Thêm ngày nghỉ phép"""
    con = get_conn()
    cur = con.cursor()
    try:
        cur.execute("""
            INSERT INTO employee_leave(emp_id, leave_date, reason)
            VALUES (%s, %s, %s)
        """, (emp_id, leave_date, reason))
        con.commit()
        
        return True, f"✅ Đã thêm ngày nghỉ phép: {leave_date.strftime('%d/%m/%Y')}"
        
    except mysql.connector.IntegrityError:
        return False, f"❌ Nhân viên đã có lịch nghỉ vào ngày {leave_date.strftime('%d/%m/%Y')}"
    except Exception as e:
        return False, f"❌ Lỗi: {e}"
    finally:
        try:
            cur.close()
        finally:
            con.close()


def get_leave_records(start: Optional[dt.date] = None, 
                     end: Optional[dt.date] = None) -> pd.DataFrame:
    """Lấy danh sách nghỉ phép"""
    con = get_conn()
    try:
        q = "SELECT * FROM v_leave_detail"
        params = []
        where = []
        
        if start and end:
            where.append("leave_date BETWEEN %s AND %s")
            params += [start, end]
        elif start:
            where.append("leave_date >= %s")
            params.append(start)
        elif end:
            where.append("leave_date <= %s")
            params.append(end)
        
        if where:
            q += " WHERE " + " AND ".join(where)
        q += " ORDER BY leave_date DESC"
        
        df = pd.read_sql_query(q, con, params=params)
    finally:
        con.close()
    
    return df


def get_leave_by_employee(emp_id: int) -> pd.DataFrame:
    """Lấy danh sách nghỉ phép của 1 nhân viên"""
    con = get_conn()
    try:
        df = pd.read_sql_query("""
            SELECT id, leave_date, reason, created_at
            FROM employee_leave
            WHERE emp_id = %s
            ORDER BY leave_date DESC
        """, con, params=(emp_id,))
    finally:
        con.close()
    
    return df


def delete_leave(leave_id: int) -> Tuple[bool, str]:
    """Xóa bản ghi nghỉ phép"""
    con = get_conn()
    cur = con.cursor()
    try:
        cur.execute("DELETE FROM employee_leave WHERE id=%s", (leave_id,))
        con.commit()
        
        if cur.rowcount > 0:
            return True, "✅ Đã xóa ngày nghỉ phép"
        return False, "❌ Không tìm thấy bản ghi"
        
    except Exception as e:
        return False, f"❌ Lỗi xóa: {e}"
    finally:
        try:
            cur.close()
        finally:
            con.close()


def is_employee_on_leave(emp_id: int, check_date: dt.date = None) -> bool:
    """Kiểm tra nhân viên có nghỉ phép không"""
    if check_date is None:
        check_date = dt.date.today()
    
    con = get_conn()
    cur = con.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) FROM employee_leave
            WHERE emp_id = %s AND leave_date = %s
        """, (emp_id, check_date))
        
        count = cur.fetchone()[0]
        return count > 0
        
    finally:
        try:
            cur.close()
        finally:
            con.close()


# ============================================================================
# TIỆN ÍCH
# ============================================================================

def get_database_stats() -> Dict:
    """Lấy thống kê tổng quan hệ thống"""
    con = get_conn()
    cur = con.cursor(dictionary=True)
    try:
        stats = {}
        
        cur.execute("SELECT COUNT(*) as count FROM employees")
        stats['total_employees'] = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM attendance")
        stats['total_attendance'] = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM employee_leave")
        stats['total_leaves'] = cur.fetchone()['count']
        
        cur.execute("""
            SELECT COUNT(DISTINCT emp_id) as count
            FROM attendance
            WHERE DATE(ts) = CURDATE() AND scan_type = 'IN'
        """)
        stats['present_today'] = cur.fetchone()['count']
        
        return stats
    finally:
        try:
            cur.close()
        finally:
            con.close()