# Kiểm thử bản refactor

5 test Qt/SQLite chạy đạt với PyQt5 5.15.11 trên Linux offscreen:

- Khởi tạo database mới, maximized, trang chính đúng một QPushButton và không có QLabel.
- Chọn khoảng ngày hợp lệ/không hợp lệ.
- Bấm nút → chọn ngày → chọn folder; import và re-import qua worker/controller mới.
- Hủy chọn ngày không khởi động import.
- Đóng cửa sổ trong lúc khởi tạo không hủy QThread đang chạy.

Mẫu thử chứa 1 Serial và 3 NULL, kết quả slot 37, QTY=1, TEST_COUNT=3,
SCRAPCODE=NULL. Re-import thay 1 dòng, không tăng số lượng.

Đã đối chiếu byte: 15 file backend/dữ liệu từ ZIP gốc giữ nguyên, bao gồm
database/li_app.db, schema, reader, service, repository và worker import.
Mọi test sử dụng database tạm, không ghi vào database đính kèm.

Chưa kiểm thử hộp thoại native Windows, SMB/UNC công ty hoặc khối lượng log sản xuất.
Các test backend từ phiên bản trước không có trong ZIP người dùng gửi;
bản refactor không tuyên bố đã chạy lại những test đó.
