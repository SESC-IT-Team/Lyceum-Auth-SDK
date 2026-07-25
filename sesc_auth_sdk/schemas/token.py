from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_validator

from sesc_auth_sdk.enums.scope import Scope

class ExchangeCodeRequest(BaseModel):
    code: str
    state: str

class TokenResponse(BaseModel):
    access_token: str | None = None
    token_type: str
    scope: str
    expires_in: int
    id_token: str

class AuthentikTokenResponse(BaseModel):
    access_token: str
    token_type: str
    scope: str
    expires_in: int
    id_token: str
    refresh_token: str | None = None

class LogoutResponse(BaseModel):
    refresh_token_revoked: bool

class AccessTokenPayload(BaseModel):
    iss: str
    sub: UUID
    iat: int
    auth_time: int
    exp: int
    scope: list[Scope]
    acr: str
    amr: list[str] | None = None
    sid: str | None = None
    jti: str
    name: str | None = None
    given_name: str | None = None
    preferred_name: str | None = None
    nickname: str | None = None
    groups: list[str] | None = None
    azp: str
    uid: str
    nonce: str | None = None

    @field_validator("scope", mode="before")
    @classmethod
    def split_space_separated_string(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return v.split()
        return v

class IdTokenPayload(BaseModel):
    sub: UUID
    iss: str
    iat: int
    auth_time: int
    exp: int
    acr: str
    amr: list[str]
    sid: str
    jti: str
    name: str | None = None
    given_name: str | None = None
    preferred_name: str | None = None
    nickname: str | None = None
    groups: list[str] | None = None
    nonce: str | None = None

class TokenHeaders(BaseModel):
    kid: str
    alg: str
    typ: Literal['JWT']
