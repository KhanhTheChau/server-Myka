import os
import logging
import aiohttp
import asyncio
from core.rag_engine import RAGEngine
from core.llm_engine import LLMEngine

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.rag = RAGEngine()
        self.llm = LLMEngine()
        self.chat_history = {} # Lưu trữ lịch sử chat theo group/user

    async def send_message(self, text: str, chat_id: str = None):
        target_chat = chat_id or self.chat_id
        if not self.bot_token or not target_chat:
            logging.warning("Telegram Bot Token or Chat ID is missing. Cannot send message.")
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        logging.error(f"Telegram error: {await response.text()}")
        except Exception as e:
            logging.error(f"TelegramNotifier error: {e}")

    async def send_rag_notification(self, question: str, ai_answer: str, rag_data: dict):
        rag_answer = rag_data.get("answer", "Không có")
        
        sources_list = rag_data.get("references") or rag_data.get("sources") or rag_data.get("docs") or rag_data.get("chunks") or []
        
        source_text = ""
        if isinstance(sources_list, list) and len(sources_list) > 0:
            for idx, src in enumerate(sources_list):
                if isinstance(src, dict):
                    title = src.get("title") or src.get("file_name") or src.get("name") or src.get("document_name") or f"Nguồn {idx+1}"
                    import urllib.parse
                    title = urllib.parse.unquote(title)
                    page = src.get("page")
                    page_info = f" (Trang {page + 1})" if page is not None else ""
                    
                    url = src.get("url")
                    if url:
                        source_text += f"- <a href='{url}'>{title}{page_info}</a>\n"
                    else:
                        source_text += f"- {title}{page_info}\n"
                elif isinstance(src, str):
                    source_text += f"- {src}\n"
        
        if not source_text:
            source_text = "Không có thông tin minh chứng cụ thể.\n"

        msg = f"🤖 <b>THÔNG BÁO MYKA RAG</b>\n\n"
        msg += f"<b>❓ Câu hỏi của Ngoại:</b>\n{question}\n\n"
        msg += f"<b>💡 Trả lời của Myka:</b>\n{ai_answer}\n\n"
        msg += f"<b>📚 Trích xuất RAG:</b>\n{rag_answer}\n\n"
        msg += f"<b>🔗 Minh chứng:</b>\n{source_text}"
        
        if len(msg) > 4000:
            msg = msg[:4000] + "...\n(Tin nhắn đã bị cắt ngắn)"

        await self.send_message(msg)

    def extract_sources_text(self, rag_data: dict) -> str:
        sources_list = rag_data.get("references") or rag_data.get("sources") or rag_data.get("docs") or rag_data.get("chunks") or []
        source_text = ""
        if isinstance(sources_list, list) and len(sources_list) > 0:
            source_text = "\n\n🔗 <b>Tham khảo:</b>\n"
            for idx, src in enumerate(sources_list):
                if isinstance(src, dict):
                    title = src.get("title") or src.get("file_name") or src.get("name") or src.get("document_name") or f"Nguồn {idx+1}"
                    import urllib.parse
                    title = urllib.parse.unquote(title)
                    page = src.get("page")
                    page_info = f" (Trang {page + 1})" if page is not None else ""
                    
                    url = src.get("url")
                    if url:
                        source_text += f"- <a href='{url}'>{title}{page_info}</a>\n"
                    else:
                        source_text += f"- {title}{page_info}\n"
        return source_text

    async def start_polling(self):
        if not self.bot_token:
            logging.warning("No TELEGRAM_BOT_TOKEN found. Telegram polling is disabled.")
            return

        logging.info("Bắt đầu lắng nghe tin nhắn Telegram (Polling)...")
        offset = None
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"

        async with aiohttp.ClientSession() as session:
            # Lấy offset mới nhất để bỏ qua các tin nhắn cũ tồn đọng khi restart server
            try:
                async with session.get(url, params={"timeout": 1}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        updates = data.get("result", [])
                        if updates:
                            offset = updates[-1]["update_id"] + 1
            except Exception as e:
                logging.warning(f"Không thể clear tin nhắn cũ: {e}")

            while True:
                params = {"timeout": 30}
                if offset:
                    params["offset"] = offset

                try:
                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            updates = data.get("result", [])
                            for update in updates:
                                offset = update["update_id"] + 1
                                await self.process_update(update)
                        else:
                            await asyncio.sleep(2)
                except Exception as e:
                    logging.error(f"Lỗi khi lấy tin nhắn Telegram: {e}")
                    await asyncio.sleep(5)

    async def process_update(self, update: dict):
        message = update.get("message")
        if not message:
            return

        text = message.get("text", "")
        if not text:
            return

        if "myka" not in text.lower():
            return

        chat_id = message["chat"]["id"]
        sender_name = message["from"].get("first_name", "Ngoại")

        if chat_id not in self.chat_history:
            self.chat_history[chat_id] = []

        logging.info(f"[Telegram] Nhận tin nhắn từ {sender_name}: {text}")

        # Thông báo đang gõ
        typing_url = f"https://api.telegram.org/bot{self.bot_token}/sendChatAction"
        async with aiohttp.ClientSession() as session:
            await session.post(typing_url, json={"chat_id": chat_id, "action": "typing"})

        # Chuyển history nội bộ sang định dạng RAG
        rag_history = [{"role": msg["role"], "content": msg["content"]} for msg in self.chat_history[chat_id]]

        # Làm sạch câu hỏi (bỏ từ khóa Myka để RAG tìm kiếm chính xác hơn)
        import re
        clean_query = re.sub(r'(?i)\bmyka\b', '', text).strip()
        if not clean_query:
            clean_query = text  # Fallback nếu câu chỉ có mỗi chữ myka

        # 1. Tra cứu RAG kèm History
        rag_data = await self.rag.query(clean_query, chat_history=rag_history)
        rag_info = None
        has_rag_answer = False

        if rag_data and rag_data.get("success"):
            rag_info = rag_data.get("data", {})
            status = rag_info.get("status")
            if status != "no_match" and rag_info.get("answer"):
                has_rag_answer = True

        # Gửi LLM cùng với lịch sử (dạng text ngắn gọn)
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.chat_history[chat_id][-4:]])
        
        if has_rag_answer:
            rag_answer = rag_info.get("answer")
            ai_response = f"Dạ thưa {sender_name},\n\n{rag_answer}"
            
            # Gắn thêm minh chứng
            sources_text = self.extract_sources_text(rag_info)
            final_response = ai_response + sources_text
            
            await self.send_message(final_response, chat_id=chat_id)
            
            # Cập nhật lịch sử
            self.chat_history[chat_id].append({"role": "user", "content": text})
            self.chat_history[chat_id].append({"role": "assistant", "content": ai_response})
            
        else:
            llm_prompt = f"Ngữ cảnh trò chuyện trước đó:\n{history_text}\n\n" if history_text else ""
            llm_prompt += f"Người hỏi tên là {sender_name} trên Telegram.\n"
            llm_prompt += f"Câu hỏi hiện tại: {text}\n\n"
            llm_prompt += "Hướng dẫn cực kỳ quan trọng:\n"
            llm_prompt += "- Nếu đây chỉ là câu chào hỏi, lời cảm ơn hoặc giao tiếp thông thường (như 'chào buổi sáng', 'cảm ơn cháu', 'có khỏe không'), hãy trả lời thân thiện và bình thường, TUYỆT ĐỐI KHÔNG tag bác sĩ.\n"
            llm_prompt += "- CHỈ KHI NÀO đây là câu hỏi tìm kiếm kiến thức, bệnh lý, thuốc men, hay nghiệp vụ phức tạp mà bạn không biết do không có thông tin từ RAG, hãy BẮT BUỘC tag @QTrung2k0 vào để nhờ bác sĩ hỗ trợ."
            
            ai_response, _ = await self.llm.generate_response(llm_prompt)
            await self.send_message(ai_response, chat_id=chat_id)
            
            # Cập nhật lịch sử
            self.chat_history[chat_id].append({"role": "user", "content": text})
            self.chat_history[chat_id].append({"role": "assistant", "content": ai_response})
        
        # Giữ lịch sử không quá dài (giữ 6 tin nhắn gần nhất = 3 lượt trao đổi)
        if len(self.chat_history[chat_id]) > 6:
            self.chat_history[chat_id] = self.chat_history[chat_id][-6:]
