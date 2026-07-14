from pydantic import BaseModel


class AuthorizationUrlResponse(BaseModel):
    authorization_url: str
