import asyncio
from fastapi import HTTPException
from typing import Any

from aiohttp import ClientSession, ClientTimeout

from sesc_auth_sdk.config import settings
from sesc_auth_sdk.schemas.jwk import JwksResponse
from sesc_auth_sdk.schemas.user import UserSchema


class RequestsService:
    @staticmethod
    async def request(
            path: str,
            method: str = "GET",
            retries: int = 3,
            timeout: int = 5,
            backoff_factor: float = 0.5,
            expected_status: int = 200,
            **kwargs
    ) -> Any:
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=ClientTimeout(total=timeout)) as session:
                    async with session.request(method, settings.auth_base_url + path, **kwargs) as response:
                        if response.status != expected_status:
                            if response.status == 401:
                                raise HTTPException(response.status)
                            if response.status == 403:
                                raise HTTPException(response.status, response.reason)
                            raise Exception(f"Unexpected status: {response.status}")
                        return await response.json()
            except HTTPException:
                raise
            except Exception as e:
                if attempt == retries - 1:
                    raise HTTPException(500, str(e))
                delay = backoff_factor * (2 ** attempt)
                await asyncio.sleep(delay)

    @staticmethod
    async def authorized_only_request(
            path: str,
            token: str,
            method: str = "GET",
            retries: int = 3,
            timeout: int = 5,
            backoff_factor: float = 0.5,
            expected_status: int = 200,
            **kwargs
    ):
        kwargs.update({'headers': {'Authorization': f'Bearer {token}'}})
        return await RequestsService.request(path, method, retries, timeout, backoff_factor, expected_status, **kwargs)

    @staticmethod
    async def get_jwks() -> JwksResponse:
        return JwksResponse(**(await RequestsService.request('/api/v1/auth/jwks')))

    @staticmethod
    async def get_me(token: str) -> UserSchema:
        return UserSchema(**(await RequestsService.authorized_only_request('/api/v1/auth/me', token)))
