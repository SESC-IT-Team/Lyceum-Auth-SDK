from typing import Any

from jose import JWTError

from sesc_auth_sdk.schemas.token import AuthentikTokenResponse
from sesc_auth_sdk.services.jwks_manager import JWKSManager
from sesc_auth_sdk.services.requests_service import RequestsService
from sesc_auth_sdk.settings import TokenValidationSettings
from sesc_auth_sdk.settings.m2m_settings import M2MSettings


class M2MAuthService:
    def __init__(self, settings: M2MSettings):
        self._settings = settings
        self._access_token: str | None = None
        self._jwks_manager: JWKSManager = JWKSManager(TokenValidationSettings(allowed_issuers=[settings.issuer]))

    async def _is_current_token_valid(self) -> bool:
        if self._access_token is None:
            return False
        try:
            await self._jwks_manager.verify_access_token(self._access_token)
        except JWTError:
            return False
        return True

    async def _update_token(self) -> None:
        res = AuthentikTokenResponse(**(await RequestsService.m2m_authorize(self._settings.authentik_url, self._settings.client_id, self._settings.service_account_username,
                                                                            self._settings.service_account_app_password, self._settings.scope)))
        self._access_token = res.access_token

    def _access_token_except_none(self) -> str:
        if self._access_token is None:
            raise Exception('Unexpected error')
        return self._access_token

    async def get_access_token(self) -> str:
        if not await self._is_current_token_valid():
            await self._update_token()
        return self._access_token_except_none()

    async def make_request(self, url: str,
                           method: str = "GET",
                           retries: int = 3,
                           timeout: int = 5,
                           backoff_factor: float = 0.5,
                           expected_status: int = 200,
                           **kwargs) -> Any:
        token = await self.get_access_token()
        return await RequestsService.authorized_request(url, token, method, retries,
                                                        timeout, backoff_factor,
                                                        expected_status, **kwargs)

__all__ = ["M2MAuthService"]
