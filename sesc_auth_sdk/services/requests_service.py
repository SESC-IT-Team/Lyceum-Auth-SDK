from aiohttp import ClientSession

from sesc_auth_sdk.config import settings
from sesc_auth_sdk.schemas.jwk import JwksResponse
from sesc_auth_sdk.schemas.user import UserSchema


class RequestsService:
    @staticmethod
    async def get_jwks() -> JwksResponse:
        res: JwksResponse
        async with ClientSession() as session:
            async with session.get(settings.auth_base_url + '/api/v1/auth/jwks') as response:
                res = JwksResponse(**(await response.json()))
        return res

    @staticmethod
    async def get_me(token: str) -> UserSchema:
        res: UserSchema
        async with ClientSession() as session:
            session.headers.update({'Authorization': f'Bearer {token}'})
            async with session.get(settings.auth_base_url + '/api/v1/auth/me') as response:
                res = UserSchema(**(await response.json()))
        return res
