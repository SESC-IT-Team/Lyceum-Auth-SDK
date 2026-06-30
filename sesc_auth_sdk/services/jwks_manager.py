import asyncio
from datetime import datetime, timedelta

import jwt
from jose import JWTError

from sesc_auth_sdk.config import settings
from sesc_auth_sdk.schemas.jwk import Jwk
from sesc_auth_sdk.schemas.access_token import AccessTokenHeaders, AccessTokenPayload
from sesc_auth_sdk.schemas.user import JwtUserSchema
from sesc_auth_sdk.services.requests_service import RequestsService

class JWKSManagerClass:
    _ttl = timedelta(seconds=settings.jwks_ttl)

    def __init__(self):
        self._prev_update_time: dict[str, datetime] = {}
        self._keys: dict[str, dict[str, Jwk]] = {}

    async def get_key(self, iss: str, kid: str) -> Jwk | None:
        if self._prev_update_time.get(iss) and self._prev_update_time[iss] + self._ttl < datetime.now():
            await self.update_keys()
        try:
            return self._keys[iss][kid]
        except KeyError:
            await self.update_keys(iss)
            return self._keys[iss].get(kid)

    async def update_keys(self, iss: str):
        keys_dict = {}
        keys_list = (await RequestsService.get_jwks(iss)).keys
        for key in keys_list:
            keys_dict[key.kid] = key
        self._keys[iss] = keys_dict
        self._prev_update_time[iss] = datetime.now()

    async def verify_token(self, token: str) -> AccessTokenPayload:
        try:
            unverified_headers = AccessTokenHeaders(**jwt.get_unverified_header(token))
            kid = unverified_headers.kid
            if not kid:
                raise JWTError("Field kid missed in headers of token")
            iss = jwt.decode(token, options={"verify_signature": False}).get('iss')
            if iss not in settings.allowed_issuers:
                raise JWTError("Token issued by untrusted issuer")
            key = await self.get_key(iss, kid)
            if not key:
                raise JWTError("Public key not found in JWKS")
            return AccessTokenPayload(**jwt.decode(token, jwt.PyJWK(key.model_dump()), algorithms=["RS256"], options={'verify_exp': True, "verify_signature": True}))
        except JWTError:
            raise
        except Exception as e:
            raise JWTError(f'Error occurred while verifying token: {str(e)}')

jwks_manager = JWKSManagerClass()
