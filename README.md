# 🧠 Myka AI Server Backend

Chào mừng đến với Bộ não Đám mây (Cloud Brain) của Robot Myka. Đây là một máy chủ bất đồng bộ (Asynchronous Server) được viết hoàn toàn bằng Python, có nhiệm vụ giao tiếp thời gian thực (Real-time) với vi điều khiển ESP32 thông qua giao thức WebSocket.

Máy chủ này đóng vai trò là "Nhạc trưởng" điều phối toàn bộ hệ sinh thái AI, biến những tín hiệu âm thanh thô sơ (Raw PCM) từ ESP32 trở thành một chuỗi hội thoại có cảm xúc.

---

## ⚡ Các Tính năng Nổi bật

- **Full-Duplex WebSocket:** Truyền tải dữ liệu âm thanh nhị phân (Binary Streaming) hai chiều không độ trễ, loại bỏ hoàn toàn Overhead của HTTP.
- **Microservice AI Đa tầng:**
  - **Nhận diện giọng nói (STT):** Sử dụng `SpeechRecognition` để dịch nguyên âm thanh (PCM 16kHz Mono) thành văn bản.
  - **Tư duy Ngôn ngữ (LLM):** Sử dụng `Google Gemini 1.5 Flash` qua SDK chính thức để xử lý văn bản, tạo ra câu trả lời và tự động gán nhãn Cảm xúc (Emotion).
  - **Truy vấn Dữ liệu (RAG):** Tích hợp RAG nội bộ công ty để cung cấp thông tin chính xác theo tài liệu nghiệp vụ/y tế.
  - **Tổng hợp Giọng nói (TTS):** Sử dụng `Microsoft Edge-TTS` để chuyển câu trả lời thành giọng nói sinh động.
- **Tích hợp Đa Nền tảng (Omnichannel):**
  - Hỗ trợ trò chuyện trực tiếp qua **Telegram Group** (Sử dụng cơ chế Long Polling).
  - Hỗ trợ trả lời tự động qua **WhatsApp** (Sử dụng Webhook qua cổng `5001`).
- **Xử lý Đồng thời (Concurrency) & Ép xung thời gian (Throttling):** Máy chủ có khả năng xử lý đa luồng bất đồng bộ (Asyncio) giúp duy trì đồng thời WebSocket, Telegram và WhatsApp mà không bị nghẽn (Blocking). Việc chạy song song luồng âm thanh và luồng suy nghĩ giúp giấu kín hoàn toàn độ trễ của AI.
- **Xử lý Cục bộ (Local Intent Detection):** Nhận diện trực tiếp các lệnh cơ bản (như "tạm biệt", "đi ngủ") ở tầng STT bằng toán tử `in` để giảm thiểu việc gọi API không cần thiết.
- **Tự động Ghi nhật ký (Conversation Logging):** Lưu lại mọi hội thoại giữa Robot và Người dùng vào file `chat_history.log` để tiện tra cứu và kiểm duyệt.

---

## ⚙️ Hướng dẫn Cài đặt & Khởi chạy

### 1. Yêu cầu Hệ thống
- Hệ điều hành: Windows, macOS, hoặc Linux (khuyến nghị chạy trên Raspberry Pi hoặc Edge Server).
- Ngôn ngữ: **Python 3.10** trở lên.

### 2. Cài đặt Thư viện
Mở Terminal tại thư mục `server/` và chạy lệnh sau để tự động cài đặt tất cả thư viện cần thiết:
```bash
pip install -r requirements.txt
```

### 3. Cấu hình Bảo mật & Môi trường
Dự án áp dụng tiêu chuẩn bảo mật biến môi trường để tuyệt đối không rò rỉ API Key lên Github. Hệ thống hỗ trợ 2 môi trường: `local` (chạy trên máy cá nhân) và `production` (chạy trên máy chủ thực tế).
1. Đổi tên file `.env.example` thành `.env.local` (cho máy tính của bạn) hoặc `.env.production` (cho server).
2. Mở file vừa tạo và điền đầy đủ các thông tin: **Gemini API Key**, **RAG Config**, **Telegram Bot**, và **WhatsApp Meta Token**.
*(Lưu ý: Các file `.env.*` đã được đưa vào `.gitignore` để bảo vệ an toàn)*.

### 4. Khởi động Máy chủ (Local Development)
```bash
# Ở máy Local, hệ thống mặc định sẽ đọc file .env.local
python server.py
```
Khi chạy, Terminal sẽ hiển thị các luồng hoạt động song song và sẽ in ra toàn bộ log để bạn dễ dàng gỡ lỗi (Debug).

### 5. Triển khai lên Production (Docker)
Để triển khai lên VPS hoặc máy chủ thực tế mà không cần cấu hình Python thủ công, chỉ cần dùng Docker:
1. Đảm bảo bạn đã điền đủ thông tin vào file `.env.production`.
2. Chạy lệnh:
```bash
docker-compose up -d --build
```
Hệ thống sẽ tự động build image, tối ưu hóa log (chỉ in lỗi), và giữ server luôn chạy ngầm dù máy chủ có khởi động lại.

---

## 📁 Cấu trúc Thư mục

```text
server/
├── core/
│   ├── config.py           # Quản lý cấu hình động (Local vs Prod) và biến môi trường.
│   ├── client_session.py   # Máy phát trạng thái của ESP32. Xử lý luồng WAKE/SLEEP/SPEAKING.
│   ├── llm_engine.py       # Quản lý Gemini API và trích xuất Cảm xúc.
│   ├── rag_engine.py       # Xử lý kết nối với API RAG nội bộ của công ty.
│   ├── phrase_manager.py   # Hệ thống Cache MP3 cho các câu giao tiếp cơ bản.
│   ├── stt_engine.py       # Quản lý Speech-to-Text cục bộ.
│   ├── tts_engine.py       # Tích hợp Edge-TTS.
│   ├── telegram_notifier.py # Bot Telegram tương tác trong Group, có trí nhớ hội thoại.
│   └── whatsapp_notifier.py # Bot WhatsApp qua Webhook (Port 5001).
├── audio_cache/            # Thư mục sinh tự động lưu trữ các file âm thanh.
├── .env.local              # File cấu hình bảo mật chạy trên máy cá nhân.
├── .env.production         # File cấu hình bảo mật chạy trên máy chủ thực tế.
├── Dockerfile              # Script đóng gói máy chủ.
├── docker-compose.yml      # Cấu hình triển khai chạy ngầm bằng Docker.
├── requirements.txt        # Danh sách thư viện Python.
└── server.py               # Entry point - Khởi chạy WebSocket (5000) và Webhook (5001).
```

---

## 🤝 Đóng góp và Mở rộng
Mô hình hiện tại (ClientSession) đã được tối ưu cho kiến trúc đa luồng (Multi-threading). Để Scale-up dự án, bạn hoàn toàn có thể thay thế class `LLMEngine` bằng một local model (như `llama.cpp`) hoặc đổi `STTEngine` sang Whisper API mà không làm thay đổi bất kỳ logic giao tiếp nào với Robot ESP32.
