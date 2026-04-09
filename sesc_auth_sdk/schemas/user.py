from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from sesc_auth_sdk.enums.department import Department
from sesc_auth_sdk.enums.gender import Gender
from sesc_auth_sdk.enums.permission import Permission
from sesc_auth_sdk.enums.role import Role
from sesc_auth_sdk.schemas.jwt import JwtPayload


class UserSchema(BaseModel):
    id: UUID
    last_name: str
    first_name: str
    middle_name: str | None
    role: Role
    gender: Gender
    class_name: str | None
    graduation_year: int | None
    login: str
    departments: list[Department] | None
    created_at: datetime
    updated_at: datetime

class JwtUserSchema(BaseModel):
    id: UUID
    role: Role
    permissions: list[Permission]

    @staticmethod
    def from_jwt_payload(payload: JwtPayload):
        return JwtUserSchema(id=payload.sub, role=payload.role, permissions=payload.permissions)
