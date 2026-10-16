# Tool TL - CLOUD 🚀

[![Version](https://img.shields.io/badge/version-1.3.1-blue.svg)](file:///VERSION)

Phần mềm chuyên nghiệp quản lý, đồng bộ dữ liệu doanh nghiệp, kiểm tra liên kết OneDrive và tạo mã QR tự động cho Công ty TNHH Tư vấn & Dịch vụ Thuế TL.

---

## 📖 HƯỚNG DẪN SỬ DỤNG PHẦN MỀM CHO NGƯỜI DÙNG (VISUAL USER GUIDE)

### 1. Yêu cầu môi trường & Cài đặt
- Hệ điều hành: Windows 10 / Windows 11.
- Python 3.10+ kèm môi trường ảo `.venv`:
```powershell
# Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1

# Cài đặt thư viện nếu chưa có
pip install -r requirements.txt

# Chạy ứng dụng
python TLCLOUD.py
```

---

### 2. Bảng Tra Cứu Chi Tiết Từng Nút Bấm & Thao Tác (Button-by-Button Map)

| Nút bấm / Điều khiển | Vị trí trên giao diện | Mục đích sử dụng | Hướng dẫn thao tác chi tiết | Kết quả sau khi bấm |
| :--- | :--- | :--- | :--- | :--- |
| **Ô tìm kiếm "Mã số thuế / Tên công ty"** | Thanh công cụ trên cùng | Tra cứu nhanh thông tin doanh nghiệp | Nhập MST hoặc tên công ty (có gợi ý tìm kiếm) | Bảng lọc danh sách doanh nghiệp khớp điều kiện |
| **Hộp chọn "Năm làm việc"** | Cạnh ô tìm kiếm | Chọn niên độ kế toán cần thao tác | Chọn năm (2024, 2025, 2026...) | Cập nhật cấu trúc thư mục theo năm đã chọn |
| **[Dọn Rác & Đồng Bộ Cloud]** | Khung Thao tác Đơn vị | Dọn file tạm và đẩy dữ liệu lên máy chủ | Chọn 1 công ty trong danh sách $\rightarrow$ Bấm nút | Tự động loại bỏ cache/file tạm và đồng bộ an toàn |
| **[Đồng Bộ Toàn Bộ]** | Khung Đồng bộ hệ thống | Đồng bộ toàn bộ các đơn vị cùng lúc | Bấm nút $\rightarrow$ Xác nhận hộp thoại | Hệ thống chạy worker ngầm đồng bộ toàn diện |
| **[Sao Chép Ra USB]** | Khung Quản lý Thiết bị | Bàn giao dữ liệu cho khách hàng/nhân sự | Cắm USB vào máy $\rightarrow$ Chọn ổ đĩa USB $\rightarrow$ Bấm nút | Format/Copy dữ liệu và ghi nhật ký bàn giao |
| **[Kiểm Tra OneDrive]** | Tab Double Check | Kiểm tra đường dẫn liên kết đám mây | Bấm nút kiểm tra | Quét toàn bộ MST và báo cáo các link bị đứt gãy |
| **[Tạo Mã QR Offline]** | Tab Tiện ích QR | Sinh mã QR nhanh từ danh sách dữ liệu | Nhập nội dung hoặc nạp file $\rightarrow$ Bấm nút | Tạo ảnh mã QR lưu vào thư mục chỉ định |

---

### 3. Xử Lý Sự Cố Thường Gặp (Troubleshooting)
- **Lỗi không nhận diện ổ USB**: Kiểm tra lại cổng cắm USB, đảm bảo USB hiển thị trong Windows Explorer và có đủ quyền đọc/ghi.
- **Lỗi OneDrive chưa đồng bộ**: Kiểm tra icon OneDrive dưới khay hệ thống Windows xem có đang bị Pause Sync hoặc lỗi đăng nhập không.
- **Lỗi xung đột dữ liệu SQLite**: Không mở file database `.db` bằng phần mềm ngoài khi `TLCLOUD.py` đang chạy.

---

## 🧭 ĐIỀU HƯỚNG TÀI LIỆU
- 🧠 **[Kiến trúc hệ thống code (SYSTEM.md)](file:///SYSTEM.md)**: Chi tiết kiến trúc module, schema SQLite và xử lý đa luồng PyQt6.
- 📜 **[Lịch sử thay đổi (CHANGELOG.md)](file:///CHANGELOG.md)**: Nhật ký cập nhật phiên bản.
