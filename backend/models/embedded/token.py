from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class RefreshTokenEmbedded(BaseModel):
    token: str
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    userAgent: Optional[str] = None
   