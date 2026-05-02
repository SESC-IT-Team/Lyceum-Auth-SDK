from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from sesc_auth_sdk.config import settings
from sesc_auth_sdk.enums.permission import PermissionType
from sesc_auth_sdk.schemas.user import UserSchema, JwtUserSchema
from sesc_auth_sdk.services.jwks_manager import jwks_manager
from sesc_auth_sdk.services.requests_service import RequestsService

security_bearer = HTTPBearer(auto_error=False)


class LyceumAuth:
    '''fastapi dependency, that allows only authorized users that have required permissions to endpoint'''

    def __init__(self, required_permissions: list[PermissionType] | None = None):
        self._required_permissions = required_permissions

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
        if settings.use_statics:
            return settings.static_jwt_user
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        try:
            return await jwks_manager.verify_token(token)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    async def __call__(self, jwt_user: JwtUserSchema = Depends(verify_authorized)) -> JwtUserSchema:
        if self._required_permissions and not all(
                permission in jwt_user.permissions for permission in self._required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Some required permissions are missing. User permissions: {jwt_user.permissions}, required permissions: {self._required_permissions}.'
            )
        return jwt_user

    async def return_user(self, token: str = Depends(_get_token),
                          token_payload: JwtUserSchema = Depends(verify_authorized)) -> UserSchema:
        """makes dependency return full user information"""
        await self(token_payload)
        if settings.use_statics:
            return settings.static_user
        return await RequestsService.get_me(token)

    async def check_strict_and_return_user(self, token: str = Depends(_get_token),
                                           token_payload: JwtUserSchema = Depends(verify_authorized)) -> UserSchema:
        """additionally check that the user object has required permissions and makes dependency return full user information"""
        user = await self.return_user(token, token_payload)
        if self._required_permissions and not all(
                permission in self._required_permissions for permission in user.permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Some required permissions are missing. User permissions: {user.permissions}, required permissions: {self._required_permissions}.'
            )
        return user
