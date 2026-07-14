from sesc_auth_sdk.settings.base_settings import Settings

class TokenValidationSettings(Settings):
    jwks_ttl: int = 900
    allowed_issuers: list[str]
