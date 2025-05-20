from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Union, TYPE_CHECKING, ForwardRef
from pydantic import Field, BaseModel, ConfigDict, field_validator, EmailStr,ValidationInfo
from beanie import Document, PydanticObjectId, Link
from pymongo import IndexModel
from pathlib import Path
import pytz



class UserResponseBase(BaseModel):
    id: str = Field(alias="_id")
    username: str
    email: Optional[str] = None 
    avatar: str
    notifications: 'NotificationsEmbedded'
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    role: str
    currentSubscription: Optional['CurrentSubscriptionEmbedded'] = None 
    wallet: 'WalletEmbedded' = Field(default_factory=lambda: WalletEmbedded())
    history: List['SubscriptionHistoryResponse'] = Field(default_factory=list) 
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={object: str, datetime: lambda v: v.isoformat()}
    )



class CreateUserRequest(BaseModel):
    username: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)
    confirmPassword: str
    notifications: Optional['NotificationsEmbedded'] = Field(default_factory=lambda: NotificationsEmbedded())

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



try:
    from backend.models.embedded.notification import NotificationsEmbedded
    from backend.models.embedded.subscription import CurrentSubscriptionEmbedded
    from backend.models.embedded.wallet import WalletEmbedded
    from backend.schemas.subscription import SubscriptionHistoryResponse, SubscriptionPlanResponse
    
    UserResponseBase.model_rebuild() 
    CreateUserRequest.model_rebuild()
    UpdateUserRequest.model_rebuild() 
    LoginUserRequest.model_rebuild()
except ImportError as e:
    import logging
    logging.warning(f"Could not update forward refs: {e}")