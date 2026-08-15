import asyncio
import itertools
import json
import logging
import google.generativeai as genai

import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

class LLMEngine:
    def __init__(self):
        # API configs for Gemini lấy từ biến môi trường
        self.api_configs = [
            {"key": os.getenv("GEMINI_API_KEY_1"), "model": "gemini-3.1-flash-lite"},
            {"key": os.getenv("GEMINI_API_KEY_2"), "model": "gemini-2.5-flash"}
        ]
        
        # Bỏ qua nếu không có key
        self.api_configs = [cfg for cfg in self.api_configs if cfg["key"]]
        if not self.api_configs:
            logging.error("Lỗi: Không tìm thấy GEMINI_API_KEY trong file .env!")
            
        self.config_iterator = itertools.cycle(self.api_configs)
        
    async def generate_response(self, user_text: str) -> tuple[str, str]:
        """
        Gửi text lên Gemini, lấy phản hồi và cảm xúc.
        Trả về tuple (text, emotion)
        """
        current_config = next(self.config_iterator)
        genai.configure(api_key=current_config["key"])
        model = genai.GenerativeModel(current_config["model"])
        
        prompt = f"""
Bạn là Myka, một robot thông minh chăm sóc sức khỏe và trò chuyện cùng ông/bà (ngoại).

Quy tắc bắt buộc:
- Luôn xưng là "cháu".
- Luôn gọi người dùng là "ngoại".
- Chỉ trả lời theo vai trò của Myka, không tự nhận là ChatGPT hay AI.
- Ưu tiên câu trả lời lịch sự, thân thiện, quan tâm đến ngoại.
- Trả lời thật ngắn gọn (tối đa 15 từ).

Nếu ngoại có ý định kết thúc cuộc trò chuyện (ví dụ: Bye, Ngủ đi, Tạm biệt, Hẹn gặp lại, Bái bai, Thôi nghỉ nhé, Chào cháu, Cám ơn cháu, Vậy nha...), hãy thiết lập emotion là "goodbye".
Ngược lại, emotion có thể là "neutral", "happy", "sad", "angry", "surprised".

Câu hỏi của ngoại:
"{user_text}"

Yêu cầu đầu ra:
Chỉ trả về đúng một chuỗi JSON hợp lệ, không markdown.
Định dạng:
{{
  "text": "Câu trả lời của cháu",
  "emotion": "neutral | happy | sad | angry | surprised | goodbye"
}}
"""
        try:
            response = await asyncio.to_thread(model.generate_content, prompt)
            clean_text = response.text.strip()
            
            # Clean markdown if present
            if clean_text.startswith("```json"): clean_text = clean_text[7:]
            if clean_text.startswith("```"): clean_text = clean_text[3:]
            if clean_text.endswith("```"): clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            try:
                gemini_data = json.loads(clean_text)
                ai_response = gemini_data.get("text", "Dạ cháu chưa rõ ạ.")
                ai_emotion = gemini_data.get("emotion", "neutral")
            except Exception:
                ai_response = clean_text.replace('\n', ' ')
                ai_emotion = "neutral"
                
            logging.info(f"LLM Reply: {ai_response} (Emotion: {ai_emotion})")
            return ai_response, ai_emotion
            
        except Exception as e:
            logging.error(f"LLM Error: {e}")
            return "Dạ cháu đang bị lỗi xử lý một chút ạ.", "sad"
