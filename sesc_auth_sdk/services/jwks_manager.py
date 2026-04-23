import asyncio
from datetime import datetime, timedelta

import jwt
from jose import JWTError

from sesc_auth_sdk.config import settings
from sesc_auth_sdk.schemas.jwk import Jwk
from sesc_auth_sdk.schemas.jwt import JwtHeaders, JwtPayload
from sesc_auth_sdk.schemas.user import JwtUserSchema
from sesc_auth_sdk.services.requests_service import RequestsService

class JWKSManagerClass:
    _ttl = timedelta(seconds=settings.jwks_ttl)

    def __init__(self):
        self._prev_update_time: datetime = datetime.now()
        self._keys: dict[str, Jwk] = {}
        self.update_keys()

    async def get_key(self, kid: str):
        if self._prev_update_time + self._ttl < datetime.now():
            await self.update_keys()
        try:
            return self._keys[kid]
        except KeyError:
            await self.update_keys()
            return self._keys.get(kid)

    async def update_keys(self):
        keys_dict = {}
        keys_list = (await RequestsService.get_jwks()).keys
        for key in keys_list:
            keys_dict[key.kid] = key
        self._keys = keys_dict
        self._prev_update_time = datetime.now()

    async def verify_token(self, token: str) -> JwtUserSchema:
        try:
            unverified_headers = JwtHeaders(**jwt.get_unverified_header(token))
            kid = unverified_headers.kid
            if not kid:
                raise JWTError("Field kid missed in headers of token")
            key = await self.get_key(kid)
            if not key:
                raise JWTError("Public key not found in JWKS")
            return JwtUserSchema.from_jwt_payload(JwtPayload(**jwt.decode(token, jwt.PyJWK(key.model_dump()), algorithms=["RS256"], options={'verify_exp': True, "verify_signature": True})))
        except JWTError:
            raise
        except Exception as e:
            raise JWTError(f'Error occurred while verifying token: {str(e)}')

jwks_manager = JWKSManagerClass()
