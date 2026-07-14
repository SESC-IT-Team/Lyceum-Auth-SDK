from abc import abstractmethod, ABC
from typing import Coroutine, Callable, Any, ClassVar

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from pydantic_settings.sources.providers import aws

from sesc_auth_sdk.services.requests_service import RequestsService
from sesc_auth_sdk.enums.scope import Scope
from sesc_auth_sdk.schemas.token import AccessTokenPayload
from sesc_auth_sdk.schemas.user import User
from sesc_auth_sdk.services.jwks_manager import JWKSManager

security_bearer = HTTPBearer(auto_error=False)


def create_jwks_manager_dependency(jwks_manager: JWKSManager) -> Callable[[],Coroutine[Any, Any, JWKSManager]]:
    async def _get_jwks() -> JWKSManager:
        return jwks_manager
    return _get_jwks

class LyceumAuth(ABC):
    """fastapi dependency, that allows only authorized users that have required permissions to endpoint"""


    user_service_url: ClassVar[str]

    @staticmethod
    @abstractmethod
    async def _get_jwks_manager() -> JWKSManager:
        ...

    def __init__(self, required_scopes: list[Scope] | None = None):
        self._required_scopes = required_scopes

    @staticmethod
    async def _get_token(
            request: Request,
            credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer)
    ) -> str | None:
        if credentials and credentials.credentials:
            return credentials.credentials
        return request.cookies.get("access_token")

    @staticmethod
    async def verify_authorized(token: str | None = Depends(_get_token), jwks_manager: JWKSManager = Depends(_get_jwks_manager)) -> AccessTokenPayload:
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        try:
            return await jwks_manager.verify_access_token(token)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    async def __call__(self, token_payload: AccessTokenPayload = Depends(verify_authorized)) -> AccessTokenPayload:
        if self._required_scopes and not all(
                scope in token_payload.scope for scope in self._required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Some required scopes are missing. User permissions: {token_payload.scope}, required permissions: {self._required_scopes}.'
            )
        return token_payload

    @classmethod
    async def get_current_user(cls, token: str):
        return User(**(await RequestsService.authorized_request(cls.user_service_url + '/me', token)))

    async def return_user(self, token_payload: AccessTokenPayload = Depends(verify_authorized), token: str = Depends(_get_token)):
        await self(token_payload)
        return await self.get_current_user(token)




