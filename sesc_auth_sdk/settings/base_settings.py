from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    _env_file: str | None = None
    _env_prefix: str | None = None

__all__ = ["Settings"]
