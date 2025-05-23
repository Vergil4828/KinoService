from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Union, TYPE_CHECKING
from pydantic import Field, BaseModel, ConfigDict, field_validator, EmailStr,ValidationInfo
from beanie import Document, PydanticObjectId, Link
from pymongo import IndexModel
from pathlib import Path
import pytz

from backend.models.embedded.notification import NotificationsEmbedded
from backend.models.embedded.wallet import WalletEmbedded
from backend.models.embedded.subscription import CurrentSubscriptionEmbedded
from backend.models.embedded.token import RefreshTokenEmbedded

class User(Document):
    username: str
    email: str
    password: str 
    avatar: str = "/defaults/default-avatar.png"
    notifications: NotificationsEmbedded = Field(default_factory=NotificationsEmbedded)
    currentSubscription: Optional[CurrentSubscriptionEmbedded] = Field(default_factory=CurrentSubscriptionEmbedded)
    wallet: WalletEmbedded = Field(default_factory=WalletEmbedded)
    role: str = Field(default="user", description="User role", examples=["user", "admin"])
    refreshTokens: List[RefreshTokenEmbedded] = Field(default_factory=list) 
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={PydanticObjectId: str}
    )

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", 1)], name="email_1", unique=True, background=True),
            IndexModel([("refreshTokens.createdAt", 1)], name="refreshTokens.createdAt_1", background=True, expireAfterSeconds=604800),
            IndexModel([("refreshTokens.token", 1)], name="refreshTokens_token_1", background=True),
        ]
        use_state_management = True

    async def before_save(self):
        if self.id is None or (self.id is not None and self.get_original_state() is None):
             if self.createdAt is None:
                  self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)


