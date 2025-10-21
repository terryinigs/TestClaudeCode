"""設定管理"""
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


class Settings(BaseSettings):
    """應用程式設定"""
    youtube_api_key: str = ""
    output_dir: Path = Path("./output")
    temp_dir: Path = Path("./temp")
    clip_buffer_seconds: int = 2
    video_quality: str = "720p"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def ensure_dirs(self):
        """確保目錄存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


# 全域設定實例
settings = Settings()
