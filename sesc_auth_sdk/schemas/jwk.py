from pydantic import BaseModel


class Jwk(BaseModel):
    kty: str
    kid: str
    use: str
    alg: str
    n: str
    e: str


class JwksResponse(BaseModel):
    keys: list[Jwk]
