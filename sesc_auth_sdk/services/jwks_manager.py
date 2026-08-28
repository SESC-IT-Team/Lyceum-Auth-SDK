from datetime import datetime, timedelta

import jwt
from jose import JWTError

from sesc_auth_sdk.settings import TokenValidationSettings
from sesc_auth_sdk.schemas.jwk import Jwk
from sesc_auth_sdk.schemas.token import TokenHeaders, AccessTokenPayload, IdTokenPayload
from sesc_auth_sdk.services.requests_service import RequestsService
from logging import getLogger

logger = getLogger(__name__)



class JWKSManager:
    def __init__(self, settings: TokenValidationSettings):
        self._prev_update_time: dict[str, datetime] = {}
        self._keys: dict[str, dict[str, Jwk]] = {}
        self._settings = settings

    @property
    def _jwks_ttl(self) -> timedelta:
        return timedelta(seconds=self._settings.jwks_ttl)

    async def get_key(self, iss: str, kid: str) -> Jwk | None:
        if self._prev_update_time.get(iss) and self._prev_update_time[iss] + self._jwks_ttl < datetime.now():
            await self.update_keys(iss)
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

    async def _verify_token[T: AccessTokenPayload | IdTokenPayload](self, payload_type: type[T], token: str) -> T:
        try:
            unverified_headers = TokenHeaders(**jwt.get_unverified_header(token))
            kid = unverified_headers.kid
            if not kid:
                logger.warning(f"Invalid token headers")
                raise JWTError("Field kid missed in headers of token")
            iss: str = payload_type(**jwt.decode(token, options={"verify_signature": False})).iss
            if iss not in self._settings.allowed_issuers:
                raise JWTError(f"Token issued by untrusted issuer, {iss=}")
            key = await self.get_key(iss, kid)
            if not key:
                raise JWTError("Public key not found in JWKS")
            return payload_type(**jwt.decode(token, jwt.PyJWK(key.model_dump()), algorithms=["RS256"], options={'verify_exp': True, "verify_signature": True, 'verify_aud': False}))
        except JWTError:
            raise
        except Exception as e:
            raise JWTError(f'Error occurred while verifying token: {str(e)}')

    async def verify_access_token(self, token: str) -> AccessTokenPayload:
        return await self._verify_token(AccessTokenPayload, token)

    async def verify_id_token(self, token: str) -> IdTokenPayload:
        return await self._verify_token(IdTokenPayload, token)

__all__ = ["JWKSManager"]
