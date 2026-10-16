# 📜 LỊCH SỬ THAY ĐỔI (CHANGELOG)

Tất cả các thay đổi đáng chú ý của dự án này sẽ được ghi nhận tại đây theo từng phiên bản.

---

## [1.3.1] - 2026-10-16

### 🚀 Fixed & Improved
- **Sửa lỗi crash khi triển khai Onedir trên NAS**: Khắc phục triệt để lỗi `Can't determine version for pytz` do tàn dư thư mục rác `_internal\pytz` từ các bản build cũ gây xung đột namespace package với pandas.
- **Tối ưu quy trình đồng bộ NAS**: Làm sạch hoàn toàn thư mục thư viện `_internal` trên máy chủ NAS (`\\nastl\TL\...`), bảo toàn 100% dữ liệu danh mục SQLite và cấu hình `config.json`.
- **Sao lưu an toàn**: Tự động tạo thư mục sao lưu cơ sở dữ liệu và mã QR trước khi nâng cấp.
- **Chuẩn hóa Quad-Docs**: Bổ sung bộ 4 tài liệu tiêu chuẩn gồm `README.md`, `SYSTEM.md`, `VERSION`, `CHANGELOG.md`.

---

## [1.3.0] - 2026-09-21

### 🚀 Added
- Nâng cấp giao diện người dùng PyQt6 hiện đại, hỗ trợ dark/light mode và autocomplete tra cứu MST.
- Tích hợp tính năng Double Check đồng bộ OneDrive và báo cáo liên kết đứt gãy.
- Chức năng dọn rác, đồng bộ dữ liệu đám mây và kết xuất dữ liệu sang ổ đĩa USB an toàn.
- Hỗ trợ phát sinh mã QR offline doanh nghiệp.

---

## [1.0.0] - 2026-04-07

### 🚀 Added
- Khởi tạo dự án công cụ quản trị dữ liệu nội bộ TL CLOUD.
- Quản lý danh sách thuế và thông tin doanh nghiệp qua cơ sở dữ liệu SQLite theo từng niên độ.
