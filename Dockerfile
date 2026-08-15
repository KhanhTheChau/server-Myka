FROM python:3.10-slim

# Cài đặt thư viện hệ thống cần thiết (ví dụ: ffmpeg cho audio, build-essential cho aiohttp)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép file requirements và cài đặt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn
COPY . .

# Xóa các file/thư mục không cần thiết cho production (nếu vô tình copy vào)
RUN rm -rf test_*.py get_chat_id.py whatsapp-bot .env.local || true

# Khai báo các port sẽ mở (WebSocket và Webhook)
EXPOSE 5000
EXPOSE 5001

# Thiết lập biến môi trường mặc định là production
ENV APP_ENV=production

# Chạy server
CMD ["python", "server.py"]
