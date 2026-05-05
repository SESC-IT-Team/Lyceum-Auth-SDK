from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from sesc_auth_sdk.enums.gender import Gender
from sesc_auth_sdk.enums.permission import PermissionType
from sesc_auth_sdk.enums.role import Role
from sesc_auth_sdk.schemas.jwt import JwtPayload


class UserSchema(BaseModel):
    id: UUID
    last_name: str
    first_name: str
    middle_name: str | None
    roles: list[Role]
    gender: Gender
    class_name: str | None
    graduation_year: int | None
    login: str
    permissions: list[PermissionType]
    created_at: datetime
    updated_at: datetime

class JwtUserSchema(BaseModel):
    id: UUID
    roles: list[Role]
    permissions: list[PermissionType]

    @staticmethod
    def from_jwt_payload(payload: JwtPayload):
        return JwtUserSchema(id=payload.sub, roles=payload.roles, permissions=payload.permissions)
