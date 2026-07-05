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
    application_slug: str | None = None
    login_redirect_uri: str | None = None

    cookie_domain: str | None = None
    cookie_secure: bool = False
    cookie_samesite: str = 'lax'

    refresh_token_ttl: int = 2592000 # 30 days
    access_token_ttl: int = 300 # 5 mins
    oauth_initial_oauth_code_flow_cookies_ttl: int = 300 # 5 mins

    send_access_token_in_json_response: bool = True
    send_access_token_as_cookie: bool = False

settings = AuthSDKConfig()