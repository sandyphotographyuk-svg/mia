"""Centralised configuration loaded from environment (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    MIA_ENV: str = "development"
    MIA_SECRET_KEY: str = "change-me"
    MIA_API_HOST: str = "0.0.0.0"
    MIA_API_PORT: int = 8000

    DATABASE_URL: str = "sqlite:///./mia.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:7b"
    OLLAMA_TIMEOUT_SECONDS: int = 120

    HUGGINGFACE_API_KEY: str = ""
    HF_IMAGE_MODEL: str = "black-forest-labs/FLUX.2-klein-4B"
    HF_IMAGE_ENDPOINT: str = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.2-klein-4B"
    MIA_OUTPUTS_DIR: str = "outputs"

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    GENERIC_WEBHOOK_URL: str = ""
    DESKTOP_NOTIFY_ENABLED: bool = True


settings = Settings()
