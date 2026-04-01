import jwt
from jose import JWTError

from sesc_auth_sdk.config import settings
from sesc_auth_sdk.schemas.jwk import Jwk
from sesc_auth_sdk.schemas.jwt import JwtHeaders, JwtPayload
from sesc_auth_sdk.services.requests_service import RequestsService

class JWKSManagerClass:
    def __init__(self):
        self._keys: dict[str, Jwk] = {}

    def get_key(self, kid: str):
        try:
            return self._keys[kid]
        except KeyError:
            self.update_keys()
            return self._keys.get(kid)

    async def update_keys(self):
        self._keys.clear()
        keys = (await RequestsService.get_jwks()).keys
        for key in keys:
            self._keys[key.kid] = key

    def verify_token(self, token: str) -> JwtPayload:
        try:
            unverified_headers = JwtHeaders(**jwt.get_unverified_header(token))
            kid = unverified_headers.kid
            if not kid:
                raise JWTError("Field kid missed in headers of token")
            key = self.get_key(kid)
            if not key:
                raise JWTError("Public key not found in JWKS")
            return JwtPayload(**jwt.decode(token, jwt.PyJWK(key.model_dump()), algorithms=["RS256"], issuer=settings.auth_base_url, options={'verify_iss': True, 'verify_exp': True, "verify_signature": True}))
        except JWTError:
            raise
        except Exception as e:
            raise JWTError(f'Error occurred while verifying token: {str(e)}')

jwks_manager = JWKSManagerClass()
