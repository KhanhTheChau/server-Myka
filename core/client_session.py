import asyncio
import json
import logging
import os
import websockets
import aiohttp
from datetime import datetime
from core.stt_engine import STTEngine
from core.llm_engine import LLMEngine
from core.tts_engine import TTSEngine
from core.phrase_manager import PhraseManager
from core.telegram_notifier import TelegramNotifier
from core.rag_engine import RAGEngine

class ClientSession:
    def __init__(self, websocket, stt: STTEngine, llm: LLMEngine, tts: TTSEngine, phrase: PhraseManager):
        self.websocket = websocket
        self.stt = stt
        self.llm = llm
        self.tts = tts
        self.phrase = phrase
        
        self.audio_buffer = bytearray()
        self.state = "SLEEP"  # SLEEP or AWAKE
        self.log_file = "chat_history.log"
        
        self.rag = RAGEngine()
        self.telegram = TelegramNotifier()
        
    def log_conversation(self, user_text: str, robot_text: str, emotion: str = ""):
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                emotion_str = f" ({emotion})" if emotion else ""
                f.write(f"[{timestamp}] Ngoại: \"{user_text}\"\n")
                f.write(f"[{timestamp}] Cháu{emotion_str}: \"{robot_text}\"\n")
                f.write("-" * 50 + "\n")
        except Exception as e:
            logging.error(f"Failed to write log: {e}")


            
    async def start(self):
        try:
            async for message in self.websocket:
                if isinstance(message, bytes):
                    self.audio_buffer.extend(message)
                else:
                    try:
                        data = json.loads(message)
                        if data.get("action") == "end_of_speech":
                            logging.info(f"Received end_of_speech. Audio size: {len(self.audio_buffer)} bytes. State: {self.state}")
                            if len(self.audio_buffer) > 0:
                                # Start a background task so websocket can continue receiving if needed
                                # However, robot pauses VAD while waiting/speaking, so we can await directly.
                                await self.process_audio()
                            self.audio_buffer.clear()
                    except json.JSONDecodeError:
                        logging.error("Invalid JSON from ESP32")
        except websockets.exceptions.ConnectionClosed as e:
            logging.info(f"WebSocket closed: {e}")
            
    async def stream_audio_file(self, file_path: str, wav_path: str = None):
        """Stream a PCM file to ESP32 and play WAV on PC."""
        if wav_path and os.path.exists(wav_path):
            try:
                import winsound
                logging.info(f"Đang phát loa PC (demo): {wav_path}")
                winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except ImportError:
                pass

        if not os.path.exists(file_path):
            logging.error(f"Audio file not found: {file_path}")
            return
            
        logging.info(f"Streaming audio to ESP32: {file_path}")
        start_time = asyncio.get_event_loop().time()
        bytes_sent = 0
        
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                await self.websocket.send(chunk)
                bytes_sent += len(chunk)
                
                # Điều tiết tốc độ gửi chính xác theo thời gian thực (32000 bytes/s cho 16kHz 16-bit Mono)
                expected_time = bytes_sent / 32000.0
                elapsed_time = asyncio.get_event_loop().time() - start_time
                if expected_time > elapsed_time:
                    await asyncio.sleep(expected_time - elapsed_time)

    async def process_audio(self):
        pcm_data = bytes(self.audio_buffer)
        
        if self.state == "SLEEP":
            text = await self.stt.recognize_audio(pcm_data)
            if not text:
                await self.websocket.send(json.dumps({"action": "ERROR"}))
                return
                
            if self.stt.contains_wake_word(text):
                logging.info("Wake word detected! Switching to AWAKE.")
                self.state = "AWAKE"
                
                phrase_text, audio_path, wav_path = self.phrase.get_random_phrase_audio("wake")
                await self.websocket.send(json.dumps({
                    "action": "WAKE_UP",
                    "text": phrase_text
                }))
                await self.stream_audio_file(audio_path, wav_path)
            else:
                logging.info("No wake word. Ignoring.")
                # Gửi ERROR để giải phóng ESP32 khỏi trạng thái PROCESSING
                await self.websocket.send(json.dumps({"action": "ERROR"}))
                
        elif self.state == "AWAKE":
            # 1. Phát câu "đang suy nghĩ" ngay lập tức để robot phản hồi nhanh
            phrase_text, audio_path, wav_path = self.phrase.get_random_phrase_audio("thinking")
            await self.websocket.send(json.dumps({
                "action": "THINKING",
                "text": "..."
            }))
            
            # Chạy ngầm việc phát âm thanh "đang suy nghĩ" để Server tranh thủ gọi STT và LLM
            thinking_task = asyncio.create_task(self.stream_audio_file(audio_path, wav_path))
            
            # 2. Chuyển giọng nói thành văn bản
            text = await self.stt.recognize_audio(pcm_data)
            if not text:
                thinking_task.cancel() # Hủy phát tiếng bíp nếu có lỗi
                await self.websocket.send(json.dumps({"action": "ERROR"}))
                return
                
            if self.stt.contains_sleep_word(text):
                thinking_task.cancel() # Hủy phát tiếng bíp
                logging.info("Sleep word detected locally! Bypassing LLM. Switching to SLEEP.")
                self.state = "SLEEP"
                gb_text, gb_audio, gb_wav = self.phrase.get_random_phrase_audio("goodbye")
                self.log_conversation(text, gb_text, "goodbye")
                await self.websocket.send(json.dumps({
                    "action": "GO_TO_SLEEP",
                    "text": gb_text
                }))
                await self.stream_audio_file(gb_audio, gb_wav)
                return

            # 3. Phân tích ngữ nghĩa qua RAG & LLM
            rag_context = ""
            rag_data = await self.rag.query(text)
            rag_info = None
            if rag_data and rag_data.get("success"):
                rag_info = rag_data.get("data", {})
                answer = rag_info.get("answer")
                status = rag_info.get("status")
                if status != "no_match" and answer:
                    rag_context = f"Dựa vào thông tin sau đây từ cơ sở dữ liệu nội bộ công ty:\n{answer}\n\n"
                    
            llm_prompt = rag_context + text
            ai_response, ai_emotion = await self.llm.generate_response(llm_prompt)
            self.log_conversation(text, ai_response, ai_emotion)
            
            # Gửi thông báo Telegram nếu có phản hồi từ RAG
            if rag_info and rag_info.get("status") != "no_match" and rag_info.get("answer"):
                asyncio.create_task(self.telegram.send_rag_notification(text, ai_response, rag_info))
            
            # Hủy phát tiếng bíp (nếu vẫn đang chạy) để có thể phát câu trả lời ngay lập tức
            if not thinking_task.done():
                thinking_task.cancel()
            
            # Dự phòng LLM vẫn có thể trả về goodbye nếu câu nói lắt léo
            if ai_emotion.lower() == "goodbye":
                logging.info("Goodbye detected via LLM. Switching to SLEEP.")
                self.state = "SLEEP"
                gb_text, gb_audio, gb_wav = self.phrase.get_random_phrase_audio("goodbye")
                await self.websocket.send(json.dumps({
                    "action": "GO_TO_SLEEP",
                    "text": gb_text
                }))
                await self.stream_audio_file(gb_audio, gb_wav)
            else:
                # 4. Gửi kết quả Chat và Stream Audio
                tts_pcm_path, tts_wav_path = await self.tts.generate_pcm(ai_response)
                
                await self.websocket.send(json.dumps({
                    "action": "CHAT_RESPONSE",
                    "text": ai_response,
                    "emotion": ai_emotion
                }))
                
                if tts_pcm_path:
                    await self.stream_audio_file(tts_pcm_path, tts_wav_path)
                    self.tts.cleanup_file(tts_pcm_path)
                    self.tts.cleanup_file(tts_wav_path)
