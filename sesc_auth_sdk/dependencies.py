from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sesc_auth_sdk.enums.role import Role
from sesc_auth_sdk.schemas.jwt import JwtPayload
from sesc_auth_sdk.schemas.user import UserSchema
from sesc_auth_sdk.services.jwks_manager import jwks_manager
from sesc_auth_sdk.services.requests_service import RequestsService

security_bearer = HTTPBearer(auto_error=False)

class LyceumAuth:
    def __init__(self, allowed_roles: Optional[list[Role]] = None):
        self.allowed_roles = allowed_roles

    @staticmethod
    async def _get_token(
            request: Request,
            credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer)
    ) -> str | None:
        if credentials and credentials.credentials:
            return credentials.credentials
        return request.cookies.get("access_token")

    @staticmethod
    async def verify_authorized(token: str | None = Depends(_get_token)) -> JwtPayload:
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return jwks_manager.verify_token(token)


    async def __call__(self, token_payload: Annotated[JwtPayload, Depends(verify_authorized)]):
        if self.allowed_roles and token_payload.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{token_payload.role}' is not allowed. Allowed: {self.allowed_roles}"
            )
        return token_payload

    async def return_user(self, token: str = Depends(_get_token)) -> UserSchema:
        self()
        return RequestsService.get_me(token)

    @staticmethod
    def get_current_user(token: str = Depends(_get_token), _ = Depends(verify_authorized)) -> UserSchema:
        return RequestsService.get_me(token)

