from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from sesc_auth_sdk.enums.department import Department
from sesc_auth_sdk.enums.position import Position
from sesc_auth_sdk.enums.role import Role
from sesc_auth_sdk.schemas.user import UserSchema, JwtUserSchema
from sesc_auth_sdk.services.jwks_manager import jwks_manager
from sesc_auth_sdk.services.requests_service import RequestsService

security_bearer = HTTPBearer(auto_error=False)

class LyceumAuth:
    def __init__(self, allowed_roles: Optional[list[Role]] = None,
                 allowed_departments: Optional[list[Department]] = None,
                 required_position: Optional[Position] = None):
        self._required_permissions = None
        self._allowed_roles = allowed_roles
        self._allowed_departments = allowed_departments
        self._required_position = required_position

    @staticmethod
    async def _get_token(
            request: Request,
            credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer)
    ) -> str | None:
        if credentials and credentials.credentials:
            return credentials.credentials
        return request.cookies.get("access_token")

    @staticmethod
    async def verify_authorized(token: str | None = Depends(_get_token)) -> JwtUserSchema:
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        try:
            return await jwks_manager.verify_token(token)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")


    async def __call__(self, jwt_user: JwtUserSchema = Depends(verify_authorized)) -> JwtUserSchema:
        if self._allowed_roles and jwt_user.role not in self._allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{jwt_user.role}' is not allowed. Allowed: {self._allowed_roles}"
            )
        if self._allowed_departments and all(department not in self._allowed_departments for department in jwt_user.departments):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User departments '{jwt_user.departments}' is not allowed. Allowed: {self._allowed_departments}"
            )
        if self._required_permissions and not all(permission in self._required_permissions for permission in jwt_user.permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Some required permissions are missing. User permissions: {jwt_user.permissions}, required permissions: {self._required_permissions}.'
            )
        if self._required_position and jwt_user.position != self._required_position:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'User position {jwt_user.position} is not allowed. Required position: {self._required_position}.'
            )
        return jwt_user

    async def return_user(self, token: str = Depends(_get_token), token_payload: JwtUserSchema = Depends(verify_authorized)) -> UserSchema:
        await self(token_payload)
        return await RequestsService.get_me(token)

    @staticmethod
    async def get_current_user(token: str = Depends(_get_token), _ = Depends(verify_authorized)) -> UserSchema:
        return await RequestsService.get_me(token)