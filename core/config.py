import os
import logging
from dotenv import load_dotenv

class Config:
    @classmethod
    def load_environment(cls):
        # Xác định môi trường (mặc định là local)
        app_env = os.getenv("APP_ENV", "local").lower()
        
        # Load file .env tương ứng
        if app_env == "prod" or app_env == "production":
            env_file = ".env.production"
            cls.APP_ENV = "production"
        else:
            env_file = ".env.local"
            cls.APP_ENV = "local"
            
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"[CONFIG] Đã load cấu hình từ file: {env_file}")
        else:
            print(f"[CONFIG] Cảnh báo: Không tìm thấy file {env_file}. Đang chạy với biến môi trường hệ thống.")

    @classmethod
    def get_log_level(cls) -> int:
        if cls.APP_ENV == "production":
            return logging.WARNING
        return logging.INFO
        
    @classmethod
    def get_host(cls) -> str:
        # Ở local, có thể chạy 127.0.0.1 để an toàn, nhưng 0.0.0.0 dễ test LAN hơn.
        # Ở production, Docker yêu cầu 0.0.0.0
        return os.getenv("HOST", "0.0.0.0")
        
    @classmethod
    def get_ws_port(cls) -> int:
        return int(os.getenv("WS_PORT", "5000"))
        
    @classmethod
    def get_webhook_port(cls) -> int:
        return int(os.getenv("WEBHOOK_PORT", "5001"))
