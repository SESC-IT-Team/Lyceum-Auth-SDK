from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status

from sesc_auth_sdk.enums.role import Role
from sesc_auth_sdk.schemas.user import UserSchema


class LyceumAuth:
    def __init__(self, allowed_roles: Optional[list[Role]] = None):
        self.allowed_roles = allowed_roles

    @staticmethod
    async def _get_current_user() -> UserSchema:
        return UserSchema.model_validate({
            "id": "a84d92ad-6af1-4661-aa7f-8bbd445f680c",
            "last_name": "Admin",
            "first_name": "Admin",
            "middle_name": None,
            "role": "admin",
            "gender": "male",
            "class_name": None,
            "graduation_year": None,
            "login": "admin",
            "created_at": "2026-03-09T08:26:32.889435Z",
            "updated_at": "2026-03-09T08:26:32.889474Z"
        })

    async def __call__(self, current_user: Annotated[UserSchema, Depends(_get_current_user)]):
        if self.allowed_roles and current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' is not allowed. Allowed: {self.allowed_roles}"
            )
        return current_user
