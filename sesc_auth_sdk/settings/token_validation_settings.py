from typing import Any

from sesc_auth_sdk.settings.base_settings import Settings

class TokenValidationSettings(Settings):
    jwks_ttl: int = 900
    internal_authentik_url: str
    allowed_application_slugs: list[str]
    allowed_issuers: list[str] = []

    def model_post_init(self, context: Any, /) -> None:
        self.allowed_issuers = [f'{self.internal_authentik_url}/application/o/{slug}/' for slug in self.allowed_application_slugs]
