from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from sesc_auth_sdk.enums.permission import Permission
from sesc_auth_sdk.enums.role import Role


class JwtPayload(BaseModel):
    sub: UUID
    role: Role
    permissions: list[Permission]
    type: Literal['access']
    iss: str
    iat: int
    nbf: int

class JwtHeaders(BaseModel):
    kid: str
    alg: str
    typ: Literal['JWT']
