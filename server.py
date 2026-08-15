import asyncio
import sys
import logging
import websockets
from dotenv import load_dotenv

load_dotenv()

from core.stt_engine import STTEngine
from core.llm_engine import LLMEngine
from core.tts_engine import TTSEngine
from core.phrase_manager import PhraseManager
from core.client_session import ClientSession
from core.telegram_notifier import TelegramNotifier
from core.whatsapp_notifier import WhatsAppNotifier

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

stt_engine = STTEngine()
llm_engine = LLMEngine()
tts_engine = TTSEngine(voice="vi-VN-HoaiMyNeural", pitch="+25Hz", rate="+10%")
phrase_manager = PhraseManager(tts_engine)

async def handle_client(websocket):
    logging.info("\n[SERVER] ESP32 đã kết nối WebSocket!")
    session = ClientSession(websocket, stt_engine, llm_engine, tts_engine, phrase_manager)
    await session.start()
    logging.info("[SERVER] Đóng session ESP32.")

async def main():
    logging.info('==================================================')
    logging.info(' SERVER WEBSOCKET AI ĐÃ SẴN SÀNG (Port 5000)')
    logging.info('==================================================')
    
    # Pre-generate audio cho Phrase Manager
    await phrase_manager.pregenerate_cache()
    
    # Khởi chạy server WebSocket, Telegram Polling và WhatsApp Webhook song song
    telegram_bot = TelegramNotifier()
    asyncio.create_task(telegram_bot.start_polling())
    
    whatsapp_bot = WhatsAppNotifier()
    asyncio.create_task(whatsapp_bot.start_server())
    
    async with websockets.serve(handle_client, "0.0.0.0", 5000, ping_interval=None):
        await asyncio.Future()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server stopped by user.")
