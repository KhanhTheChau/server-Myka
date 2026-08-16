import os
import logging
import aiohttp
from aiohttp import web
import asyncio
from core.rag_engine import RAGEngine
from core.llm_engine import LLMEngine

class WhatsAppNotifier:
    def __init__(self):
        self.token = os.getenv("WHATSAPP_TOKEN")
        self.phone_number_id = os.getenv("PHONE_NUMBER_ID")
        self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "myka_secret_123")
        
        self.rag = RAGEngine()
        self.llm = LLMEngine()
        self.chat_history = {}  # Lưu lịch sử chat theo số điện thoại

    async def send_message(self, recipient_number: str, text_message: str) -> bool:
        if not self.token or not self.phone_number_id:
            logging.warning("Thiếu cấu hình WhatsApp. Không thể gửi tin nhắn.")
            return False

        base_url = f"https://graph.facebook.com/v25.0/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "text",
            "text": {"body": text_message}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(base_url, headers=headers, json=payload) as response:
                    if response.status in [200, 201]:
                        logging.info(f"[WhatsApp] Đã gửi tin nhắn tới {recipient_number}.")
                        return True
                    else:
                        logging.error(f"[WhatsApp] Lỗi gửi tin nhắn: {await response.text()}")
                        return False
        except Exception as e:
            logging.error(f"[WhatsApp] Lỗi kết nối: {e}")
            return False

    def extract_sources_text(self, rag_data: dict) -> str:
        sources_list = rag_data.get("references") or rag_data.get("sources") or rag_data.get("docs") or rag_data.get("chunks") or []
        source_text = ""
        if isinstance(sources_list, list) and len(sources_list) > 0:
            source_text = "\n\n🔗 *Tham khảo:*\n"
            for idx, src in enumerate(sources_list):
                if isinstance(src, dict):
                    title = src.get("title") or src.get("file_name") or src.get("name") or src.get("document_name") or f"Nguồn {idx+1}"
                    import urllib.parse
                    title = urllib.parse.unquote(title)
                    page = src.get("page")
                    page_info = f" (Trang {page + 1})" if page is not None else ""
                    
                    url = src.get("url")
                    if url:
                        source_text += f"- {title}{page_info}: {url}\n"
                    else:
                        source_text += f"- {title}{page_info}\n"
        return source_text

    async def verify_webhook(self, request: web.Request) -> web.Response:
        """1. Xác minh Webhook từ Meta."""
        mode = request.query.get('hub.mode')
        token = request.query.get('hub.verify_token')
        challenge = request.query.get('hub.challenge')
        
        if mode == 'subscribe' and token == self.verify_token:
            logging.info("Xác minh Webhook WhatsApp Meta thành công.")
            return web.Response(text=challenge, status=200)
        
        logging.warning("Xác minh Webhook WhatsApp Meta thất bại.")
        return web.Response(text="Xác minh thất bại", status=403)

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """2. Nhận và xử lý tin nhắn WhatsApp từ người dùng."""
        try:
            data = await request.json()
        except Exception:
            return web.Response(status=400)

        try:
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    if 'messages' in value:
                        message_info = value['messages'][0]
                        sender_phone = message_info.get('from')
                        
                        if message_info.get('type') == 'text':
                            incoming_text = message_info['text']['body']
                            
                            sender_name = "Bạn"
                            if 'contacts' in value and len(value['contacts']) > 0:
                                sender_name = value['contacts'][0].get('profile', {}).get('name', 'Bạn')
                                
                            logging.info(f"[WhatsApp] Nhận tin từ {sender_name} ({sender_phone}): {incoming_text}")
                            
                            # Xử lý tin nhắn chạy ngầm để không bị timeout webhook (Meta yêu cầu trả về 200 nhanh)
                            asyncio.create_task(self.process_message(sender_phone, sender_name, incoming_text))
                        else:
                            logging.info(f"[WhatsApp] Bỏ qua loại tin nhắn không phải text: {message_info.get('type')}")
                            
        except Exception as e:
            logging.error(f"[WhatsApp] Lỗi xử lý payload Webhook: {e}", exc_info=True)
            
        return web.json_response({"status": "ok"}, status=200)

    async def process_message(self, sender_phone: str, sender_name: str, text: str):
        if sender_phone not in self.chat_history:
            self.chat_history[sender_phone] = []

        # Chuyển history nội bộ sang định dạng RAG
        rag_history = [{"role": msg["role"], "content": msg["content"]} for msg in self.chat_history[sender_phone]]

        # Làm sạch câu hỏi
        import re
        clean_query = re.sub(r'(?i)\bmyka\b', '', text).strip()
        if not clean_query:
            clean_query = text

        # 1. Tra cứu RAG
        rag_data = await self.rag.query(clean_query, chat_history=rag_history)
        rag_info = None
        has_rag_answer = False

        if rag_data and rag_data.get("success"):
            rag_info = rag_data.get("data", {})
            status = rag_info.get("status")
            if status != "no_match" and rag_info.get("answer"):
                has_rag_answer = True

        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.chat_history[sender_phone][-4:]])
        
        if has_rag_answer:
            rag_answer = rag_info.get("answer")
            ai_response = f"Dạ thưa {sender_name},\n\n{rag_answer}"
            
            # Gắn thêm minh chứng
            sources_text = self.extract_sources_text(rag_info)
            final_response = ai_response + sources_text
            
            await self.send_message(sender_phone, final_response)
            
            self.chat_history[sender_phone].append({"role": "user", "content": text})
            self.chat_history[sender_phone].append({"role": "assistant", "content": ai_response})
            
        else:
            llm_prompt = f"Ngữ cảnh trò chuyện trước đó:\n{history_text}\n\n" if history_text else ""
            llm_prompt += f"Người hỏi tên là {sender_name} trên WhatsApp.\n"
            llm_prompt += f"Câu hỏi hiện tại: {text}\n\n"
            llm_prompt += "Hướng dẫn cực kỳ quan trọng:\n"
            llm_prompt += "- Nếu đây chỉ là câu chào hỏi, lời cảm ơn hoặc giao tiếp thông thường, hãy trả lời thân thiện và bình thường, TUYỆT ĐỐI KHÔNG nhắc đến bác sĩ.\n"
            llm_prompt += "- CHỈ KHI NÀO đây là câu hỏi tìm kiếm kiến thức, bệnh lý, thuốc men, hay nghiệp vụ phức tạp mà bạn không biết do không có thông tin, hãy báo cáo rằng bạn không rõ và sẽ ghi nhận để báo cho bác sĩ (vì WhatsApp không hỗ trợ tag tên)."
            
            ai_response, _ = await self.llm.generate_response(llm_prompt)
            await self.send_message(sender_phone, ai_response)
            
            self.chat_history[sender_phone].append({"role": "user", "content": text})
            self.chat_history[sender_phone].append({"role": "assistant", "content": ai_response})
        
        # Giữ lịch sử không quá dài
        if len(self.chat_history[sender_phone]) > 6:
            self.chat_history[sender_phone] = self.chat_history[sender_phone][-6:]

    async def start_server(self):
        if not self.token or not self.phone_number_id:
            logging.warning("No WhatsApp configuration found. WhatsApp Webhook is disabled.")
            return
            
        from core.config import Config
        host = Config.get_host()
        port = Config.get_webhook_port()

        app = web.Application()
        app.router.add_get('/webhook', self.verify_webhook)
        app.router.add_post('/webhook', self.handle_webhook)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        
        logging.info(f"WhatsApp Webhook đang chạy tại http://{host}:{port}/webhook")
        await site.start()
        
        # Giữ server chạy ngầm
        while True:
            await asyncio.sleep(3600)
