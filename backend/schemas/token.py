from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field




class RefreshTokenRequest(BaseModel):
    refreshToken: str
