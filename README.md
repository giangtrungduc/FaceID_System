# Hệ thống Chấm công Nhận diện Khuôn mặt (Face Attendance System)

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)

[cite_start]Đây là dự án Bài tập lớn môn học, xây dựng một ứng dụng chấm công thông minh sử dụng công nghệ nhận diện khuôn mặt[cite: 57]. [cite_start]Ứng dụng được phát triển bằng ngôn ngữ **Python**, sử dụng **Tkinter** cho giao diện đồ họa (GUI), **OpenCV** để xử lý camera, và thư viện `face_recognition` cho các tác vụ AI[cite: 135].

[cite_start]Hệ thống này thay thế các phương pháp chấm công truyền thống (thẻ từ, vân tay) [cite: 69][cite_start], giúp tăng tính chính xác, minh bạch và tiết kiệm thời gian [cite: 79-81].

Dự án bao gồm hai thành phần chính:
1.  [cite_start]**Admin Panel (Ứng dụng Quản trị):** Giao diện Tkinter cho phép quản lý nhân viên, đăng ký khuôn mặt, duyệt nghỉ phép và xuất báo cáo [cite: 110-114].
2.  [cite_start]**Kiosk App (Ứng dụng Chấm công):** Giao diện Tkinter với camera để nhân viên thực hiện chấm công hàng ngày [cite: 90-96].

## 🖼️ Hình ảnh Demo

| Giao diện Admin Panel | Giao diện Kiosk Chấm công |
| :---: | :---: |
| ![Giao diện Admin Panel](https://i.imgur.com/example.png) | ![Giao diện Kiosk Chấm công](https://i.imgur.com/example.png) |
| [cite_start]*(Hình ảnh Admin Panel từ [cite: 381])* | [cite_start]*(Hình ảnh Kiosk App từ )* |

*(Lưu ý: Bạn cần thay thế link `https://i.imgur.com/example.png` bằng link ảnh chụp màn hình thực tế của ứng dụng)*

## ✨ Tính năng chính

### 🧑‍💼 Tính năng Quản trị (Admin Panel)

* [cite_start]**Bảo mật:** Đăng nhập bằng tài khoản Admin đã được lưu trong CSDL[cite: 303, 380].
* [cite_start]**Quản lý Nhân viên:** Thêm, Sửa, Xóa thông tin nhân viên (Mã NV, Họ tên, Phòng ban, SĐT) [cite: 316, 381-388].
* [cite_start]**Đăng ký Khuôn mặt:** Tải ảnh khuôn mặt của nhân viên, hệ thống sẽ tự động mã hóa và lưu vector đặc trưng vào CSDL[cite: 320, 382].
* [cite_start]**Quản lý Nghỉ phép:** Thêm hoặc xóa các ngày nghỉ phép cho nhân viên [cite: 347, 389-391].
* **Báo cáo & Thống kê:**
    * [cite_start]Xem báo cáo chi tiết (từng lượt chấm công) và báo cáo tổng hợp (tính công) [cite: 358-360, 396].
    * [cite_start]Lọc báo cáo theo khoảng thời gian tùy chọn (Từ ngày - Đến ngày)[cite: 394].
    * [cite_start]**Xuất báo cáo** chi tiết và tổng hợp ra file `.csv` để lưu trữ[cite: 392, 397].

### 🧑‍🚀 Tính năng Chấm công (Kiosk App)

* [cite_start]**Camera thời gian thực:** Hiển thị hình ảnh trực tiếp từ webcam.
* [cite_start]**Chấm công 1-Click:** Nhân viên chỉ cần nhấn nút "Chấm công (chụp)" để thực hiện.
* **Xử lý IN/OUT tự động:**
    * [cite_start]Lần quét đầu tiên trong ngày được ghi nhận là **"Giờ vào" (IN)**[cite: 342].
    * [cite_start]Lần quét thứ hai trong ngày được ghi nhận là **"Giờ ra" (OUT)**[cite: 343].
* [cite_start]**Chống chấm công lặp:** Hệ thống chặn thao tác nếu nhân viên đã chấm đủ 2 lượt (IN/OUT) trong ngày[cite: 129, 176].
* [cite_start]**Phản hồi tức thì:** Hiển thị thông báo "CHẤM CÔNG THÀNH CÔNG!" kèm Tên, Mã NV, và thời gian ngay trên màn hình.

## 🛠️ Công nghệ sử dụng

* [cite_start]**Ngôn ngữ lập trình:** Python 3.x [cite: 138]
* [cite_start]**Giao diện (GUI):** Tkinter [cite: 140]
* [cite_start]**Xử lý Camera:** OpenCV [cite: 143, 145]
* [cite_start]**Nhận diện khuôn mặt:** `face_recognition` [cite: 147-148]
* [cite_start]**Cơ sở dữ liệu:** MySQL [cite: 154, 156]
* [cite_start]**Xử lý dữ liệu & Báo cáo:** Pandas [cite: 150, 152]
* [cite_start]**Hỗ trợ ảnh:** Pillow (PIL) [cite: 158, 160]
* **Tiện ích lịch (GUI):** tkcalendar