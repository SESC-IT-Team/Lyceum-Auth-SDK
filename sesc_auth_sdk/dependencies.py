from abc import abstractmethod, ABC
from typing import Coroutine, Callable, Any, ClassVar

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from pydantic_settings.sources.providers import aws

from sesc_auth_sdk.enums.role import Role
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
    async def get_jwks_manager() -> JWKSManager:
        ...

    def __init__(self, required_scopes: list[Scope] | None = None):
        self._required_scopes = required_scopes
        self._allowed_roles: list[Role] | None = None

    @staticmethod
    async def _get_token(
            request: Request,
            credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer)
    ) -> str | None:
        if credentials and credentials.credentials:
            return credentials.credentials
        return request.cookies.get("access_token")

    @classmethod
    async def verify_authorized(cls, token: str | None = Depends(_get_token)) -> AccessTokenPayload:
        jwks_manager = await cls.get_jwks_manager()
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        try:
            return await jwks_manager.verify_access_token(token)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    async def __call__(self, token: str = Depends(_get_token)) -> AccessTokenPayload:
        token_payload: AccessTokenPayload = await self.verify_authorized(token)
        if self._required_scopes and not all(
                scope in token_payload.scope for scope in self._required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Some required scopes are missing. User permissions: {token_payload.scope}, required permissions: {self._required_scopes}.'
            )
        return token_payload

    @classmethod
    async def get_current_user(cls, token: str):
        return User(**(await RequestsService.authorized_request(cls.user_service_url + '/v1/users/me', token)))

    def restrict_roles_and_return_user(self, allowed_roles: list[Role]):
        self._allowed_roles = allowed_roles
        return self.return_user

    async def return_user(self, token: str = Depends(_get_token)):
        await self(token)
        user = await self.get_current_user(token)
        if self._allowed_roles and not any(map(lambda r: r in self._allowed_roles, user.roles)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has not any of allowed roles.")
        return user

    async def return_token(
            self,
            token: str = Depends(_get_token)
    ) -> str:
        await self(token)
        return token
