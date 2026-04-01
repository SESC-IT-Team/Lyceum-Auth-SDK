from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSDKConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    auth_base_url: str

settings = AuthSDKConfig()
