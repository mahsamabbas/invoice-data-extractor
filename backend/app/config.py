from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_vision_model: str = "qwen2.5vl"
    ollama_timeout_seconds: float = 120.0
    cors_origins: str = "http://localhost:3006"
    max_upload_bytes: int = 5 * 1024 * 1024
    total_tolerance: float = 0.01
    sample_invoice_path: str = ""  # env SAMPLE_INVOICE_PATH; empty = repo samples/


@lru_cache
def get_settings() -> Settings:
    return Settings()
