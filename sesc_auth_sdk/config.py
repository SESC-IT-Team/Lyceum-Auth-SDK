from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSDKConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    jwks_ttl: int = 900
    allowed_issuers: list[str]
    authentik_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None

settings = AuthSDKConfig()