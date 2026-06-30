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
            url: str,
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
                    async with session.request(method, url, **kwargs) as response:
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
            url: str,
            token: str,
            method: str = "GET",
            retries: int = 3,
            timeout: int = 5,
            backoff_factor: float = 0.5,
            expected_status: int = 200,
            **kwargs
    ):
        kwargs.update({'headers': {'Authorization': f'Bearer {token}'}})
        return await RequestsService.request(url, method, retries, timeout, backoff_factor, expected_status, **kwargs)

    @staticmethod
    async def get_jwks(iss: str) -> JwksResponse:
        return JwksResponse(**(await RequestsService.request(iss + 'jwks/')))
