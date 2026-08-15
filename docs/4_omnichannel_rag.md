# 4. Hệ thống Chatbot & RAG (Omnichannel)

Bên cạnh việc nói chuyện qua Micro ESP32, Myka hỗ trợ người dùng giao tiếp qua tin nhắn văn bản (Text) trên Telegram và WhatsApp.

## Cơ chế Đa nền tảng (Omnichannel)
Myka duy trì 2 kết nối mạng xã hội:
- **Telegram (`core/telegram_notifier.py`)**: Sử dụng Long Polling (`getUpdates`). An toàn, không cần mở port ra ngoài Internet.
- **WhatsApp (`core/whatsapp_notifier.py`)**: Sử dụng Webhook (HTTP POST) tại cổng `5001`. Yêu cầu sử dụng SSL/TLS hoặc Ngrok để kết nối với Meta.

Hai kết nối này chạy như những Background Task (Tác vụ ngầm) bằng hàm `asyncio.create_task()`, giúp chúng chạy song song với WebSocket mà không tranh giành tài nguyên.

## Trí nhớ Hội thoại (Chat History)
Để giúp Myka hiểu được ngữ cảnh (ví dụ: Câu 1 hỏi "Bệnh tiểu đường là gì?", Câu 2 hỏi "Thuốc đó uống sao?"), hệ thống duy trì một bộ nhớ ngắn hạn.

Mỗi khi người dùng nhắn tin, Myka lưu lại:
```python
self.chat_history[user_id] = [
    {"role": "user", "content": "Bệnh tiểu đường là gì?"},
    {"role": "assistant", "content": "Tiểu đường là..."}
]
```
- Giới hạn: Nhớ tối đa 6 tin nhắn gần nhất (3 lượt trao đổi).
- Toàn bộ lịch sử này được gửi ngược lên **RAG Engine** và **LLM Engine** mỗi khi có câu hỏi mới để AI hiểu bối cảnh.

## Truy xuất Dữ liệu Nội bộ (RAG)
`core/rag_engine.py` chịu trách nhiệm kết nối với API nội bộ của công ty.

1. **Authentication**: Tự động lấy JWT Token bằng `RAG_ROBOT_ID` và `RAG_DEVICE_SECRET`. Nếu token hết hạn (401), hệ thống tự động gọi API lấy lại token mới và retry.
2. **Xử lý Không Khớp (no_match Fallback)**:
   - Nếu RAG trả về kết quả tốt: Myka bóc tách câu trả lời, đồng thời trích xuất danh sách các nguồn tài liệu tham khảo (Sources/References) để đính kèm thành dạng link cuối tin nhắn.
   - Nếu RAG trả về `status: no_match`: Máy chủ kích hoạt kịch bản "Báo cáo Bác sĩ". LLM được lệnh tự tạo ra câu trả lời xin lỗi và **tag thẳng @QTrung2k0** (trên Telegram) để nhờ bác sĩ có chuyên môn giải quyết.

> [!NOTE]
> Kịch bản Tag Bác Sĩ chỉ được kích hoạt nếu câu hỏi mang tính chất nghiệp vụ. Nếu người dùng chỉ nói "Chào buổi sáng", LLM có đủ thông minh để nhận ra đây là câu giao tiếp và tự động chào lại mà không làm phiền bác sĩ.
