from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_validator

from sesc_auth_sdk.enums.role import Role
from sesc_auth_sdk.enums.scope import Scope


class AccessTokenPayload(BaseModel):
    sub: UUID
    type: Literal['access']
    iat: int
    auth_time: int
    exp: int
    scope: list[Scope]
    acr: str
    amr: list[str]
    sid: str
    jti: str
    name: str
    given_name: str
    preferred_name: str
    nickname: str
    groups: list[str]
    azp: str
    uid: str

    @field_validator("scope", mode="before")
    @classmethod
    def split_space_separated_string(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return v.split()
        return v

class AccessTokenHeaders(BaseModel):
    kid: str
    alg: str
    typ: Literal['JWT']
