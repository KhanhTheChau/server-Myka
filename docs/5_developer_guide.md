# 5. Hướng dẫn Lập trình & Mở rộng (Developer Guide)

Tài liệu này hướng dẫn cách sửa đổi mã nguồn (Source Code) dành cho lập trình viên kế nhiệm khi dự án cần Scale-up hoặc nâng cấp công nghệ.

## 1. Cấu trúc Object-Oriented (OOP)
Dự án áp dụng chặt chẽ mô hình hướng đối tượng để dễ bảo trì. Bạn có thể tìm thấy các thành phần cốt lõi trong thư mục `core/`.

Nếu bạn muốn thay đổi bất kỳ AI Engine nào (STT, TTS, LLM), bạn KHÔNG CẦN đụng vào file `client_session.py`. Bạn chỉ cần mở file Engine đó lên và sửa đổi nội dung hàm `generate_response()` hoặc `transcribe()`.

## 2. Cách thay đổi mô hình LLM (Language Model)
Mặc định hệ thống dùng `Google Gemini 1.5 Flash`. Nếu sau này Google thay đổi SDK hoặc công ty muốn chuyển sang dùng OpenAI ChatGPT (gpt-4o), bạn chỉ cần làm 2 bước:

1. Mở file `core/llm_engine.py`.
2. Thay đổi phần `import google.generativeai` thành `import openai` và viết lại logic gọi API trong hàm `generate_response`. 
> Đảm bảo hàm này vẫn trả về một Tuple chứa: `(Câu_trả_lời_Text, Nhãn_Cảm_xúc)`. Mọi hệ thống khác sẽ tự động tương thích.

## 3. Cách thêm nền tảng Chat (Omnichannel) mới
Giả sử công ty muốn tích hợp thêm Zalo hoặc Facebook Messenger:
1. Tạo một file mới `core/zalo_notifier.py` tương tự như WhatsApp.
2. Thiết lập server `aiohttp.web` nếu nền tảng đó dùng Webhook, hoặc một vòng lặp `while True:` nếu nền tảng đó dùng Polling.
3. Import `RAGEngine` và `LLMEngine` y hệt như `telegram_notifier.py` để lấy được kịch bản RAG và Trí nhớ hội thoại.
4. Mở file `server.py` và gọi lệnh chạy ngầm:
```python
zalo_bot = ZaloNotifier()
asyncio.create_task(zalo_bot.start_server())
```

## 4. Quản lý Âm thanh (Audio Cache & Throttling)
- **Phrase Manager**: Những câu nói cửa miệng như *"Tạm biệt ngoại"*, *"Ngoại chờ cháu chút"* được tạo sẵn file MP3 và lưu trong thư mục `audio_cache/`. Lần gọi tiếp theo nó sẽ không gọi API lên TTS nữa mà phát thẳng file nội bộ để tiết kiệm 100% thời gian phản hồi.
- **Throttling**: Khi gửi âm thanh (PCM) xuống ESP32, không được gửi quá nhanh khiến bộ đệm (Buffer) của ESP32 bị tràn. File `tts_engine.py` sẽ chia âm thanh thành các chunk (1024 bytes) và dùng lệnh `await asyncio.sleep(delay_time)` để gửi từ từ với tốc độ chính xác 32,000 bytes/s. Tuyệt đối không xóa lệnh sleep này!
