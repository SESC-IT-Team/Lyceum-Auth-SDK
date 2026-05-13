from datetime import datetime, date
from uuid import uuid4

from pydantic_settings import BaseSettings, SettingsConfigDict

from sesc_auth_sdk.enums.gender import Gender
from sesc_auth_sdk.enums.permission import Permissions
from sesc_auth_sdk.schemas.user import JwtUserSchema, UserSchema
from sesc_auth_sdk.enums.role import Role


class AuthSDKConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    auth_base_url: str
    jwks_ttl: int = 900
    use_statics: bool = False
    static_jwt_user: JwtUserSchema = JwtUserSchema(id=uuid4(), roles=[Role.student, Role.admin], permissions=[Permissions.Auth.Users.create, Permissions.Auth.Users.read, Permissions.Auth.Users.update, Permissions.Auth.Users.delete])
    static_user: UserSchema = UserSchema(id=uuid4(), last_name='Ivanov', first_name='Ivan', middle_name='Ivanovich', roles=[Role.student, Role.admin], gender=Gender.male, class_name='10В', graduation_year=2027, login='IvanovIvan1234567', permissions=[Permissions.Auth.Users.create, Permissions.Auth.Users.read, Permissions.Auth.Users.update, Permissions.Auth.Users.delete], created_at=datetime.now(), updated_at=datetime.now(), full_name='GOL', letter='A', grade=10, birthday=date(2026, 5, 2))
settings = AuthSDKConfig()