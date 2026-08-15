import asyncio
import speech_recognition as sr
import logging

class STTEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 150 
        self.recognizer.dynamic_energy_threshold = False
        
        self.wake_words = [
            "mica", "mi ca", "mika", "mi ka", "mai ca", "mai ka", 
            "my ca", "my ka", "mee ca", "mẹ ca", "meca", "miga", 
            "meta", "meka", "mi-ca", "my-ca", "mai-ca",
            "mì ca", "mí ca", "mỉ ca", "mĩ ca", "mỹ ca", "mỷ ca",
            "mây ca", "máy ca", "ni ca", "ly ca", "micha", "misa", 
            "mi xa", "mi sa", "bi ca", "vi ca", "ti ca", "ca", "myka", 
            "pika", "pica", "ơi", "ca ơi"
        ]
        
        self.sleep_words = [
            "ngủ đi", "ngủ thôi", "đi ngủ", "tạm biệt", "bye", "bái bai", "bai con nhé", "bai con nha",
            "thôi nghỉ", "vậy nha", "chào cháu", "cám ơn cháu", "nghỉ ngơi", "stop", "dừng",
            "hẹn gặp lại", "cút", "im đi", "nín đi", "không nói chuyện nữa", "đừng nói nữa", 
            "kết thúc", "chào nha", "tắt máy", "thoát", "end", "quit", "thôi nha", 
            "đi nghỉ đây", "không cần nữa", "bai bai", "bye bye", "tạm biệt nha", "ngủ ngon", "chúc ngủ ngon", "chúc ngoại ngủ ngon",
            "chúc con ngủ ngon", "chúc cháu ngủ ngon", "ngoại mệt rồi", "ngoại nghĩ nha", "nghĩ nha", "ngoại nghỉ nha", "nghỉ nha",
        ]
        
    async def recognize_audio(self, pcm_data: bytes) -> str:
        """
        Nhận diện giọng nói từ raw PCM data.
        pcm_data cần ở định dạng 16000Hz, 16-bit, Mono.
        """
        # Tăng âm lượng x2
        try:
            import audioop
            pcm_data = audioop.mul(pcm_data, 2, 2.0)
        except ImportError:
            logging.warning("Thiếu thư viện audioop, bỏ qua khuếch đại âm lượng")
            
        audio = sr.AudioData(pcm_data, 16000, 2)
        
        try:
            # Dùng to_thread để không block asyncio loop
            text = await asyncio.to_thread(self.recognizer.recognize_google, audio, language='vi-VN')
            logging.info(f"STT Output: '{text}'")
            return text
        except sr.UnknownValueError:
            logging.warning("STT Error: Không nghe rõ!")
            return ""
        except sr.RequestError as e:
            logging.error(f"STT Error: Không thể kết nối dịch vụ Google; {e}")
            return ""

    def contains_wake_word(self, text: str) -> bool:
        """Kiểm tra xem câu có chứa từ khóa đánh thức hay không."""
        text_lower = text.lower()
        return any(w in text_lower for w in self.wake_words)

    def contains_sleep_word(self, text: str) -> bool:
        """Kiểm tra xem câu có chứa từ khóa đi ngủ/tạm biệt hay không."""
        text_lower = text.lower()
        return any(w in text_lower for w in self.sleep_words)
