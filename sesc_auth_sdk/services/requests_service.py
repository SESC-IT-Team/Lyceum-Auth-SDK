from typing import Any
import asyncio
from fastapi import HTTPException

from aiohttp import ClientSession, ClientTimeout

from sesc_auth_sdk.schemas.jwk import JwksResponse


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
                            raise Exception(f"Unexpected status: {response.status} {await response.json()}")
                        return await response.json()
            except HTTPException:
                raise
            except Exception as e:
                if attempt == retries - 1:
                    raise HTTPException(500, str(e))
                delay = backoff_factor * (2 ** attempt)
                await asyncio.sleep(delay)

    @staticmethod
    async def authorized_request(
            url: str,
            token: str,
            method: str = "GET",
            retries: int = 3,
            timeout: int = 5,
            backoff_factor: float = 0.5,
            expected_status: int = 200,
            **kwargs
    ) -> Any:
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {token}'
        kwargs['headers'] = headers
        return await RequestsService.request(url, method, retries, timeout, backoff_factor, expected_status, **kwargs)

    @staticmethod
    async def get_jwks(iss: str) -> JwksResponse:
        return JwksResponse(**(await RequestsService.request(iss + '/jwks/')))

    @staticmethod
    async def exchange_code(authentik_url: str, code: str, code_verifier: str,
                            client_id: str, client_secret: str, login_redirect_uri: str):
        return await RequestsService.request(authentik_url + '/application/o/token/', method='POST', data={
            'grant_type': 'authorization_code',
            'code': code,
            'code_verifier': code_verifier,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': login_redirect_uri,
        })

    @staticmethod
    async def refresh_token(authentik_url: str, refresh_token: str,
                            client_id: str, client_secret: str):
        return await RequestsService.request(authentik_url + '/application/o/token/', method='POST', data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
        })

    @staticmethod
    async def revoke_refresh_token(authentik_url: str, refresh_token: str,
                                   client_id: str, client_secret:str):
        return await RequestsService.request(f'{authentik_url}/application/o/revoke/', method='POST', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'token': refresh_token,
            'token_type_hint': 'refresh_token'
        }, headers={'Content-Type': 'application/x-www-form-urlencoded'})

    @staticmethod
    async def m2m_authorize(authentik_url: str, client_id: str, username: str, app_password: str, scope: str):
        return await RequestsService.request(f'{authentik_url}/application/o/token/', method='POST', data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "username": username,
            "password": app_password,
            "scope": scope,
        }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
