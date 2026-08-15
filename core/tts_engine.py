import asyncio
import os
import time
import edge_tts
import imageio_ffmpeg
import subprocess
import logging

class TTSEngine:
    def __init__(self, voice="vi-VN-HoaiMyNeural", pitch="+25Hz", rate="+10%"):
        self.voice = voice
        self.pitch = pitch
        self.rate = rate
        
        self.audio_dir = os.path.join(os.getcwd(), "audio_cache")
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
            
    async def generate_pcm(self, text: str) -> tuple[str, str]:
        """
        Tạo TTS từ text và chuyển đổi thành raw PCM và WAV (16000Hz, 16-bit, Mono).
        Trả về tuple (pcm_path, wav_path).
        """
        timestamp = int(time.time() * 1000)
        mp3_path = os.path.join(self.audio_dir, f"tts_{timestamp}.mp3")
        pcm_path = os.path.join(self.audio_dir, f"tts_{timestamp}.pcm")
        wav_path = os.path.join(self.audio_dir, f"tts_{timestamp}.wav")
        
        try:
            # Sinh MP3 bằng edge-tts (có thử lại nếu lỗi mạng)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    tts = edge_tts.Communicate(text, self.voice, pitch=self.pitch, rate=self.rate)
                    await tts.save(mp3_path)
                    break
                except Exception as e:
                    logging.warning(f"TTS Error lần {attempt + 1} cho '{text[:20]}...': {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                    else:
                        raise e
            
            # Chuyển đổi sang PCM và WAV bằng ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            subprocess.run([
                ffmpeg_exe, "-y", "-i", mp3_path, 
                "-f", "s16le", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", pcm_path,
                "-f", "wav", "-ar", "16000", "-ac", "1", wav_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Xóa file MP3 gốc để tiết kiệm dung lượng
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
                
            return pcm_path, wav_path
            
        except Exception as e:
            logging.error(f"TTS Generation Error: {e}")
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
            if os.path.exists(pcm_path):
                os.remove(pcm_path)
            if os.path.exists(wav_path):
                os.remove(wav_path)
            return "", ""
            
    def cleanup_file(self, file_path: str):
        """Xóa file sau khi đã stream xong."""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logging.error(f"Failed to cleanup {file_path}: {e}")
