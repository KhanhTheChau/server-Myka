# 3. Giao thức Giao tiếp Phần cứng (ESP32 WebSocket Protocol)

Tài liệu này dành cho Kỹ sư Nhúng (Embedded Engineer) lập trình ESP32 để kết nối và giao tiếp với máy chủ AI Myka.

## Thông số Kỹ thuật (Specifications)
- **Giao thức**: WebSocket (`ws://[IP_SERVER]:5000`)
- **Port Mặc định**: 5000
- **Định dạng Âm thanh (Audio Format)**:
  - Kiểu dữ liệu: Raw PCM (Pulse-Code Modulation)
  - Kích thước mẫu (Sample Size): 16-bit
  - Tần số lấy mẫu (Sample Rate): 16,000 Hz
  - Số kênh (Channels): 1 (Mono)
  - Dạng nhị phân (Endianness): Little-Endian

## Luồng Trạng thái (State Machine Flow)
Giao tiếp giữa ESP32 và Server dựa trên việc gửi các **tin nhắn JSON (Text)** để chuyển đổi trạng thái, đan xen với việc gửi **âm thanh nhị phân (Binary)**.

### 1. Khởi tạo
Khi ESP32 kết nối thành công WebSocket, Server sẽ tự động gửi:
```json
{"type": "status", "state": "sleeping"}
```

### 2. Đánh thức (Wake up)
- ESP32 phát hiện âm thanh từ Micro.
- ESP32 gửi JSON báo hiệu bắt đầu thu âm:
```json
{"event": "start_audio"}
```
- Máy chủ chuyển sang trạng thái WAKE và kích hoạt Speech-To-Text (STT).

### 3. Truyền Âm thanh (Streaming)
- ESP32 liên tục gửi dữ liệu PCM nhị phân (Binary) qua WebSocket (nên chia thành các chunk nhỏ khoảng 1024 bytes/chunk).
- Máy chủ sẽ gom các chunk này lại. Ngay khi luồng âm thanh ngắt hoặc ESP32 báo dừng, máy chủ sẽ đem dịch đoạn âm thanh đó.

### 4. Kết thúc Thu âm
- Khi người dùng nói xong, ESP32 gửi JSON:
```json
{"event": "stop_audio"}
```
- Máy chủ bắt đầu xử lý LLM và RAG. Nếu phải mất thời gian suy nghĩ, máy chủ sẽ báo về ESP32 một file âm thanh "Chờ cháu chút" để phát đệm.

### 5. Phát Âm thanh (Playback)
- Khi AI có câu trả lời, máy chủ sẽ gửi kèm JSON báo hiệu loại cảm xúc (Emotion) của câu đó (để ESP32 đổi màu đèn LED hoặc chớp mắt hiển thị cảm xúc):
```json
{"type": "emotion", "value": "happy"}
```
- Ngay sau đó, máy chủ gửi dữ liệu Binary chứa giọng nói trả lời (TTS PCM 16kHz) xuống ESP32. ESP32 đẩy thẳng dữ liệu này ra Loa (I2S).
- Phát xong, máy chủ tự đưa trạng thái về `SLEEP` và kết thúc chu kỳ.
