# Hướng Dẫn Vận Hành RAG System bằng cURL (Không cần Script)

Tài liệu này cung cấp các lệnh `cURL` thuần túy để bạn có thể tương tác với RAG Backend thông qua Terminal hoặc các công cụ gọi API (Postman/Insomnia) mà không cần giữ lại bất kỳ file script python trung gian nào trong dự án.

> [!NOTE]
> **Biến môi trường cần chuẩn bị:**
> Các lệnh bên dưới sử dụng các thông tin mẫu. Hãy thay thế bằng thông tin thực tế từ file `.env.local` của bạn:
> - `ROBOT_ID`: `c867a550-4c42-4c6e-925d-8954164611e3`
> - `DEVICE_SECRET`: Lấy từ `RAG_DEVICE_SECRET`
> - `TENANT_ID`: `ihubtech_demo_tenant`
> - `DEPARTMENT_ID`: `companion_bot_topic_calm_yourself`

---

## 1. Lấy Token Đăng Nhập (Authentication)

Tất cả các API của RAG đều yêu cầu JWT Token. Đầu tiên, bạn cần gọi API Auth để lấy token.

**Lệnh cURL:**
```bash
curl -X POST "https://gateway.ihubtech.dev/api/v1/robot/auth" \
     -H "X-Tenant-ID: ihubtech_demo_tenant" \
     -H "Content-Type: application/json" \
     -d '{
           "robot_id": "c867a550-4c42-4c6e-925d-8954164611e3",
           "device_secret": "YOUR_DEVICE_SECRET"
         }'
```
**Kết quả:** Bạn sẽ nhận được chuỗi `"jwt"`. Hãy copy chuỗi này để dùng cho các bước tiếp theo (thay vào chữ `$JWT_TOKEN` bên dưới).

---

## 2. Nạp Dữ Liệu Lên Server (Upload PDF)

Để đẩy một file PDF lên Server RAG, bạn sử dụng `multipart/form-data`.

**Lệnh cURL:**
```bash
curl -X POST "https://gateway.ihubtech.dev/api/v1/ai/tenants/ihubtech_demo_tenant/departments/companion_bot_topic_calm_yourself/documents" \
     -H "Authorization: Bearer $JWT_TOKEN" \
     -H "X-Tenant-ID: ihubtech_demo_tenant" \
     -F "file=@/duong/dan/tuyet/doi/toi/file_cua_ban.pdf"
```
> [!TIP]
> Thay `@/duong/dan/tuyet/doi/toi/file_cua_ban.pdf` bằng đường dẫn thực tế tới file PDF trên máy bạn (Ký tự `@` ở đầu là bắt buộc đối với cURL khi upload file).

---

## 3. Kiểm Tra Trạng Thái Học Của Robot

Sau khi upload, Server sẽ cần thời gian xử lý (chunking, embedding). Bạn có thể gọi API sau để lấy danh sách các file đã upload và trạng thái của chúng:

**Lệnh cURL:**
```bash
curl -X GET "https://gateway.ihubtech.dev/api/v1/ai/tenants/ihubtech_demo_tenant/departments/companion_bot_topic_calm_yourself/documents" \
     -H "Authorization: Bearer $JWT_TOKEN" \
     -H "X-Tenant-ID: ihubtech_demo_tenant"
```

**Đọc kết quả:**
Trong JSON trả về, hãy để ý trường `status`:
- `processing`: Đang xử lý.
- `indexed`: Đã học xong, sẵn sàng trả lời.
- `failed`: Xử lý thất bại.

---

## 4. Test Đặt Câu Hỏi Cho Robot (RAG Query)

Khi file đã ở trạng thái `indexed`, bạn có thể test thử bằng cách gửi câu hỏi để xem Robot lấy thông tin minh chứng từ PDF như thế nào.

**Lệnh cURL:**
```bash
curl -X POST "https://gateway.ihubtech.dev/api/v1/tenants/ihubtech_demo_tenant/departments/companion_bot_topic_calm_yourself/ask" \
     -H "Authorization: Bearer $JWT_TOKEN" \
     -H "X-Tenant-ID: ihubtech_demo_tenant" \
     -H "Content-Type: application/json" \
     -d '{
           "question": "Đối tượng của Thiền Định là gì?",
           "chat_history": [],
           "session_id": "test_curl_session",
           "unit_id": "c867a550-4c42-4c6e-925d-8954164611e3",
           "robot_type": "SENIOR",
           "language": "vi"
         }'
```

**Kết quả:** API sẽ trả về JSON chứa trường `"answer"` (Câu trả lời) và mảng `"sources"` (Các nguồn minh chứng, bao gồm `file_name` và `page`).

---

## 5. Tích Hợp Telegram và WhatsApp

Hệ thống Omni-channel (Telegram/WhatsApp) đọc trực tiếp cấu hình từ `.env.local` và tự động thực hiện các thao tác lấy token/query y hệt như các lệnh cURL ở trên thông qua `core/rag_engine.py`.

Đảm bảo `.env.local` có đúng thông tin:
```env
RAG_TENANT_ID=ihubtech_demo_tenant
RAG_DEPARTMENT_ID=companion_bot_topic_calm_yourself
```
Mỗi khi người dùng nhắn tin, Myka sẽ tự động query vào database RAG của chủ đề này và gửi lại câu trả lời kèm link tham chiếu minh chứng rõ ràng.
