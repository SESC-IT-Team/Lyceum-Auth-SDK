from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from sesc_auth_sdk.enums.gender import Gender
from sesc_auth_sdk.enums.role import Role


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
    created_at: datetime
    updated_at: datetime
