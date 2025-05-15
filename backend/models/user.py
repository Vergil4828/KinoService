from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import Field, BaseModel, ConfigDict, field_validator, EmailStr,ValidationInfo
from beanie import Document, PydanticObjectId, Link
from pymongo import IndexModel
from pathlib import Path
import pytz

from .token import RefreshTokenEmbedded
from .wallet import WalletEmbedded
from .subscription import (
    CurrentSubscriptionEmbedded,
    SubscriptionHistoryResponse
)

class NotificationsEmbedded(BaseModel):
    email: bool = False
    push: bool = False
    newsletter: bool = False




class User(Document):
    username: str
    email: str
    password: str # Store hashed password!
    avatar: str = "/defaults/default-avatar.png"
    notifications: NotificationsEmbedded = Field(default_factory=NotificationsEmbedded)
    currentSubscription: Optional[CurrentSubscriptionEmbedded] = Field(default_factory=CurrentSubscriptionEmbedded)
    wallet: WalletEmbedded = Field(default_factory=WalletEmbedded)
    role: str = Field(default="user", description="User role", examples=["user", "admin"])
    refreshTokens: List[RefreshTokenEmbedded] = Field(default_factory=list) 
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

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


class UserStats(Document):
    userId: PydanticObjectId
    views: int = Field(default=0, ge=0)
    ratings: int = Field(default=0, ge=0)
    favorites: List[PydanticObjectId] = []
    watchlist: List[PydanticObjectId] = []
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


    class Settings:
        name = "userstats"
        indexes = [
            IndexModel([("userId", 1)], name="userId_1", unique=True, background=True),
        ]
        use_state_management = True

    async def before_save(self):
        if self.id is None or (self.id is not None and self.get_original_state() is None):
             if self.createdAt is None:
                  self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)


 





class UserResponseBase(BaseModel):
    id: str = Field(alias="_id")
    username: str
    email: Optional[str] = None 
    avatar: str
    notifications: NotificationsEmbedded
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    role: str
    currentSubscription: Optional[CurrentSubscriptionEmbedded] = None 
    wallet: WalletEmbedded = Field(default_factory=WalletEmbedded)
    history: List[SubscriptionHistoryResponse] = Field(default_factory=list) 
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={object: str, datetime: lambda v: v.isoformat()}
    )



class CreateUserRequest(BaseModel):
    username: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)
    confirmPassword: str
    notifications: Optional[NotificationsEmbedded] = Field(default_factory=NotificationsEmbedded)

    @field_validator('confirmPassword')
    @classmethod
    def passwords_match(cls, v: str, info: ValidationInfo) -> str: 
        if 'password' in info.data and v != info.data['password']: 
            raise ValueError('Пароли не совпадают')
        return v

class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateUserRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    currentPassword: str = Field(min_length=1)
    newPassword: Optional[str] = Field(None, min_length=8)

    @field_validator('newPassword')
    @classmethod
    def new_password_length_check(cls, v):
        return v


