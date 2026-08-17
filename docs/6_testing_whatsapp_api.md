# Hướng Dẫn Test API Gửi Tin Nhắn WhatsApp

Tài liệu này hướng dẫn cách test việc gửi tin nhắn WhatsApp thông qua công cụ **Meta Graph API Explorer**.

## 1. Chuẩn bị

1. Truy cập [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. Chọn ứng dụng của bạn (VD: Myka Bot) ở góc trên bên phải.
3. Đảm bảo bạn đã có **Mã truy cập (Access Token)** với quyền `whatsapp_business_messaging`.
4. Phương thức Request là **POST**.
5. Phiên bản API: (VD: `v26.0`).

## 2. Đường dẫn (Path)

Tại ô nhập đường dẫn ngay cạnh phương thức `POST` và phiên bản API, bạn nhập:

```text
<PHONE_NUMBER_ID>/messages
```

*Lưu ý: Thay `<PHONE_NUMBER_ID>` bằng ID số điện thoại của bạn.*

## 3. Nội dung JSON (Payload)

Chuyển sang tab **JSON** (nằm cạnh tab *Thông số* / *Params*). Dán nội dung sau vào:

### A. Mẫu cơ bản (chuẩn JSON, đã escape ký tự xuống dòng)

```json
{
  "messaging_product": "whatsapp",
  "to": "84327533788",
  "type": "text",
  "text": {
    "body": "Dựa vào nội dung tài liệu bạn đã cung cấp, câu trả lời được tóm lược và làm rõ qua hai khía cạnh chính:\n\n### 1. Khi có lời giải nghĩa hoặc sự hướng dẫn (từ Thiền Sư)\n\n* **Giúp thông suốt:** Giúp người thực hành hiểu rõ và nhận ra bản chất của vấn đề.\n* **Tâm tự động vận hành:** Một khi tâm đã thấu suốt, nó có khả năng tự động làm việc một cách nhanh chóng.\n* **Đạt kết quả nhanh:** Hỗ trợ hành giả nhanh chóng thực hiện được sự **đột phá** trong quá trình tu tập.\n\n### 2. Khi không có sự hướng dẫn từ Thiền Sư\n\n* Người thực hành có thể sẽ phải **mất rất nhiều thời gian** để có thể tiến bộ (tấn hóa) hoặc đạt được sự đột phá."
  }
}
```

### B. Mẫu tối ưu hiển thị cho WhatsApp

*Lưu ý: WhatsApp dùng `*` cho in đậm thay vì `**`, và `_` cho in nghiêng. Mã Markdown thông thường có thể hiển thị không đúng định dạng trên ứng dụng WhatsApp.*

```json
{
  "messaging_product": "whatsapp",
  "to": "84327533788",
  "type": "text",
  "text": {
    "body": "Dựa vào nội dung tài liệu bạn đã cung cấp, câu trả lời được tóm lược và làm rõ qua hai khía cạnh chính:\n\n*1. Khi có lời giải nghĩa hoặc sự hướng dẫn (từ Thiền Sư)*\n\n- *Giúp thông suốt:* Giúp người thực hành hiểu rõ và nhận ra bản chất của vấn đề.\n- *Tâm tự động vận hành:* Một khi tâm đã thấu suốt, nó có khả năng tự động làm việc một cách nhanh chóng.\n- *Đạt kết quả nhanh:* Hỗ trợ hành giả nhanh chóng thực hiện được sự *đột phá* trong quá trình tu tập.\n\n*2. Khi không có sự hướng dẫn từ Thiền Sư*\n\n- Người thực hành có thể sẽ phải *mất rất nhiều thời gian* để có thể tiến bộ (tấn hóa) hoặc đạt được sự đột phá."
  }
}
```

## 4. Ghi chú quan trọng

- JSON chuẩn không hỗ trợ xuống dòng bằng phím `Enter` hay dấu nháy 3 (`"""`). Mọi khoảng ngắt dòng bắt buộc phải được thay thế bằng ký tự `\n`.
- Số điện thoại người nhận (`to`) phải bao gồm mã quốc gia, không chứa dấu `+` (VD: Việt Nam là `84...`).
- Nếu ứng dụng đang ở chế độ Development (Thử nghiệm), số điện thoại người nhận bắt buộc phải là số đã được thêm vào danh sách **Số điện thoại thử nghiệm** trong cấu hình WhatsApp API của Meta.
