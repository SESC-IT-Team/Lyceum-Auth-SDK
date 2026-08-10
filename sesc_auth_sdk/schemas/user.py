from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel

from sesc_auth_sdk.enums.gender import Gender
from sesc_auth_sdk.enums.role import Role


class User(BaseModel):
    id: UUID
    last_name: str
    first_name: str
    middle_name: str | None
    full_name: str
    gender: Gender
    roles: list[Role]
    lives_in_dormitory: bool
    birthday: date | None
    grade: int | None
    letter: str | None
    class_name: str | None
    graduation_year: int | None
    login: str
    created_at: datetime | None
    updated_at: datetime | None