from __future__ import annotations
from pydantic import BaseModel


class RefreshTokenRequest(BaseModel):
    refreshToken: str
