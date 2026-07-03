from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from sesc_auth_sdk.config import settings

from sesc_auth_sdk.enums.scope import Scope
from sesc_auth_sdk.schemas.access_token import AccessTokenPayload
from sesc_auth_sdk.services.jwks_manager import jwks_manager

security_bearer = HTTPBearer(auto_error=False)


class LyceumAuth:
    '''fastapi dependency, that allows only authorized users that have required permissions to endpoint'''

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
    async def verify_authorized(token: str | None = Depends(_get_token)) -> AccessTokenPayload:
        if settings.use_statics:
            return settings.static_jwt_user
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        try:
            return await jwks_manager.verify_token(token)
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    async def __call__(self, token_payload: AccessTokenPayload = Depends(verify_authorized)) -> AccessTokenPayload:
        if self._required_scopes and not all(
                scope in token_payload.scope for scope in self._required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Some required scopes are missing. User permissions: {token_payload.scope}, required permissions: {self._required_scopes}.'
            )
        return token_payload
