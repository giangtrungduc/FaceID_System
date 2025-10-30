-- ============================================================================
-- SCRIPT KHỞI TẠO DATABASE CHO HỆ THỐNG CHẤM CÔNG
-- ============================================================================

-- Tạo database
CREATE DATABASE IF NOT EXISTS face_attendance 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE face_attendance;

-- ============================================================================
-- 1. BẢNG USERS (Tài khoản Admin)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 2. BẢNG EMPLOYEES (Nhân viên)
-- ============================================================================
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    phone VARCHAR(20),
    embedding LONGBLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_emp_code (emp_code),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 3. BẢNG ATTENDANCE (Chấm công)
-- ============================================================================
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id INT NOT NULL,
    ts TIMESTAMP NOT NULL,
    device VARCHAR(50),
    scan_type ENUM('IN', 'OUT') NOT NULL DEFAULT 'IN',
    FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
    INDEX idx_emp_ts (emp_id, ts),
    INDEX idx_date (ts),
    INDEX idx_scan_type (scan_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 4. BẢNG EMPLOYEE_LEAVE (Nghỉ phép)
-- ============================================================================
CREATE TABLE IF NOT EXISTS employee_leave (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id INT NOT NULL,
    leave_date DATE NOT NULL,
    reason VARCHAR(255) DEFAULT 'Nghỉ phép',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE KEY unique_emp_leave (emp_id, leave_date),
    INDEX idx_leave_date (leave_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 5. VIEW: Chi tiết nghỉ phép
-- ============================================================================
CREATE OR REPLACE VIEW v_leave_detail AS
SELECT 
    el.id,
    el.emp_id,
    e.emp_code,
    e.name AS emp_name,
    e.department,
    el.leave_date,
    el.reason,
    el.created_at
FROM employee_leave el
JOIN employees e ON el.emp_id = e.id;

-- ============================================================================
-- HOÀN TẤT
-- ============================================================================
SELECT 'Database face_attendance đã được tạo thành công!' AS Message;