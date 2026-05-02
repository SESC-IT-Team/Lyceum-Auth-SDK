from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from sesc_auth_sdk.enums.permission import PermissionType
from sesc_auth_sdk.enums.role import Role


class JwtPayload(BaseModel):
    sub: UUID
    roles: list[Role]
    permissions: list[PermissionType]
    type: Literal['access']
    iat: int
    nbf: int

class JwtHeaders(BaseModel):
    kid: str
    alg: str
    typ: Literal['JWT']
