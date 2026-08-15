import os
import random
import logging
import asyncio
from core.tts_engine import TTSEngine

class PhraseManager:
    def __init__(self, tts_engine: TTSEngine):
        self.tts_engine = tts_engine
        self.cache_dir = os.path.join(os.getcwd(), "audio_cache", "phrases")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        self.phrases = {
            "wake": [
                "Dạ, cháu đây ngoại.", "Cháu đang nghe.", "Ngoại cứ nói đi ạ.", 
                "Dạ ngoại.", "Cháu nghe đây.", "Cháu sẵn sàng rồi.", "Có cháu đây.", 
                "Cháu đây ạ.", "Dạ, ngoại cần gì ạ?", "Cháu nghe ngoại nói đây."
            ],
            "thinking": [
                "beep"
            ],
            "goodbye": [
                "Dạ cháu chào ngoại.", "Hẹn gặp lại ngoại.", "Ngoại nhớ giữ sức khỏe nha.", 
                "Khi nào cần cứ gọi cháu.", "Cháu đi nghỉ đây.", "Chúc ngoại một ngày vui vẻ.", 
                "Cháu luôn sẵn sàng khi ngoại gọi.", "Hẹn gặp ngoại sau.", "Cháu tạm biệt ngoại.", 
                "Cháu ngủ đây nha ngoại."
            ]
        }
        
    async def pregenerate_cache(self):
        """Khởi tạo: sinh sẵn các file âm thanh cho các câu thoại nếu chưa có."""
        logging.info("Bắt đầu kiểm tra và tạo cache âm thanh cho PhraseManager...")
        for category, phrase_list in self.phrases.items():
            for idx, text in enumerate(phrase_list):
                file_name = f"{category}_{idx}.pcm"
                file_path = os.path.join(self.cache_dir, file_name)
                if not os.path.exists(file_path):
                    logging.info(f"Đang sinh âm thanh: {text}")
                    # Thay vì dùng TTSEngine.generate_pcm (nó lưu vào tmppath), ta sinh thẳng vào thư mục cache
                    import edge_tts, imageio_ffmpeg, subprocess
                    mp3_path = file_path.replace(".pcm", ".mp3")
                    wav_path = file_path.replace(".pcm", ".wav")
                    
                    try:
                        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                        
                        if category == "thinking":
                            # Tạo tiếng bíp thay vì dùng TTS
                            subprocess.run([
                                ffmpeg_exe, "-y", "-f", "lavfi", "-i", "sine=frequency=800:duration=0.3",
                                "-f", "s16le", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", file_path,
                                "-f", "wav", "-ar", "16000", "-ac", "1", wav_path
                            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        else:
                            max_retries = 3
                            for attempt in range(max_retries):
                                try:
                                    tts = edge_tts.Communicate(text, self.tts_engine.voice, pitch=self.tts_engine.pitch, rate=self.tts_engine.rate)
                                    await tts.save(mp3_path)
                                    break
                                except Exception as e:
                                    logging.warning(f"Lỗi TTS lần {attempt + 1} cho '{text}': {e}")
                                    if attempt < max_retries - 1:
                                        await asyncio.sleep(2)
                                    else:
                                        raise e
                            
                            subprocess.run([
                                ffmpeg_exe, "-y", "-i", mp3_path, 
                                "-f", "s16le", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", file_path,
                                "-f", "wav", "-ar", "16000", "-ac", "1", wav_path
                            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            
                            if os.path.exists(mp3_path):
                                os.remove(mp3_path)
                    except Exception as e:
                        logging.error(f"Lỗi khi pre-generate TTS cho '{text}': {e}")
                        
        logging.info("Hoàn tất tạo cache âm thanh!")
        
    def get_random_phrase_audio(self, category: str) -> tuple[str, str, str]:
        """
        Lấy ngẫu nhiên một câu trong category.
        Trả về (text, pcm_file_path, wav_file_path).
        """
        if category not in self.phrases:
            return "", "", ""
            
        phrase_list = self.phrases[category]
        idx = random.randint(0, len(phrase_list) - 1)
        text = phrase_list[idx]
        file_path = os.path.join(self.cache_dir, f"{category}_{idx}.pcm")
        wav_path = os.path.join(self.cache_dir, f"{category}_{idx}.wav")
        
        return text, file_path, wav_path
