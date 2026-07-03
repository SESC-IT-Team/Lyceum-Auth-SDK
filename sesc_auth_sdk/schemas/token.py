from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
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

class TokenRequest(BaseModel):
    grant_type: str
    code: str | None = None
    state: str | None = None

class LogoutResponse(BaseModel):
    refresh_token_revoked: bool
