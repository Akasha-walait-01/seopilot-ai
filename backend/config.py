import sys
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# PyInstaller bundle check
if getattr(sys, "frozen", False):
    env_path = Path(sys._MEIPASS) / ".env"
else:
    env_path = Path(".env")


class Settings(BaseSettings):
    gemini_api_key: str
    database_url: str = "sqlite:///./seo_agent.db"
    backend_url: str = "http://127.0.0.1:8000"
    pagespeed_api_key: str = ""  # optional - if empty, Page Speed checks show "not configured"

    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()