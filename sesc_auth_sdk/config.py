from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSDKConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    auth_base_url: str
    auth_jwks_path: str = "/api/v1/auth/.well-known/jwks.json"
    auth_jwks_cache_ttl_seconds: int = 3600
    auth_verify_issuer: bool = True
    auth_issuer: str = "sesc-auth"

    @property
    def jwks_url(self) -> str:
        return f"{self.auth_base_url.rstrip('/')}{self.auth_jwks_path}"
