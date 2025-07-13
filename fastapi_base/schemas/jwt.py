from typing import Optional

from pydantic import BaseModel


class JWTToken(BaseModel):
    access_token: str  # O token JWT
    token_type: str  # O tipo do token, geralmente "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
