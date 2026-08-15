# 2. Hướng dẫn Triển khai & Vận hành (Deployment Guide)

Tài liệu này hướng dẫn cách cấu hình và triển khai máy chủ Myka trên cả môi trường cá nhân (Local) và máy chủ thực tế (Production).

## Quản lý Môi trường (Environment)
Dự án sử dụng cơ chế bảo mật bằng biến môi trường (Environment Variables). Hệ thống tự động phân biệt môi trường chạy thông qua biến `APP_ENV`.

- **Local (`APP_ENV=local`)**: Đọc cấu hình từ `.env.local`, hiển thị toàn bộ Log (DEBUG/INFO) để lập trình viên gỡ lỗi.
- **Production (`APP_ENV=production`)**: Đọc cấu hình từ `.env.production`, chỉ hiển thị Log Lỗi (WARNING/ERROR) để tiết kiệm tài nguyên máy chủ.

## 1. Chạy trên Local (Dành cho Lập trình viên)

### Cài đặt
1. Cài đặt Python 3.10+.
2. Mở Terminal tại thư mục gốc, cài đặt thư viện:
```bash
pip install -r requirements.txt
```
3. Đổi tên file `.env.example` thành `.env.local`.
4. Điền các API Key vào file `.env.local`.

### Khởi động
```bash
python server.py
```
Hệ thống sẽ chạy ở môi trường Local. Bạn có thể dùng `ngrok` để mở port 5001 nếu muốn test WhatsApp:
```bash
ngrok http 5001
```

## 2. Triển khai lên Production (Dành cho DevOps)

Khuyến nghị sử dụng Docker để triển khai, giúp đồng bộ hóa môi trường 100% trên mọi VPS/Cloud (AWS, DigitalOcean, Ubuntu).

### Cài đặt
1. Cài đặt `docker` và `docker-compose` trên VPS.
2. Clone source code về VPS.
3. Tạo file `.env.production` từ `.env.example` và điền đầy đủ API Key thật.

### Khởi động
Chạy lệnh sau tại thư mục gốc chứa `docker-compose.yml`:
```bash
docker-compose up -d --build
```

### Quản lý Container
- Xem log server đang chạy:
```bash
docker logs -f myka_ai_server
```
- Khởi động lại server:
```bash
docker-compose restart
```
- Dừng server:
```bash
docker-compose down
```

> [!TIP]
> **Dữ liệu bền vững (Persistent Data):**
> File `docker-compose.yml` đã được thiết lập `volumes` để mount thư mục `audio_cache/` và file `chat_history.log` ra ngoài Container. Nhờ vậy, ngay cả khi xóa Container và build lại, lịch sử chat và cache âm thanh vẫn không bị mất.
