from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import Field, BaseModel, ConfigDict
from beanie import Document, PydanticObjectId
from pymongo import IndexModel
from pydantic import field_validator

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import UserResponseBase






class AdminActionResponse(BaseModel):
    id: str = Field(alias="_id")
    adminId: PydanticObjectId 
    actionType: str
    targetModel: str
    targetId: Optional[PydanticObjectId]
    changes: Optional[Dict[str, Any]]
    ipAddress: Optional[str]
    userAgent: Optional[str]
    additionalInfo: Optional[str]
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    admin: Optional['UserResponseBase'] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={object: str, datetime: lambda v: v.isoformat()}
    )
 
 
class AdminChangePlanRequest(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Название тарифного плана",
        examples=["Премиум"]
    )
    price: float = Field(
        ...,  
        ge=0,
        description="Цена подписки",
        examples=[999]
    )
    renewalPeriod: int = Field(
        default=30,  
        ge=1,
        description="Период подписки в днях",
        examples=[30]
    )
    features: List[str] = Field(
        default_factory=list,
        description="Список возможностей подписки",
        examples=[["4K качество", "Без рекламы"]]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Премиум+",
                "price": 1199,
                "renewalPeriod": 30,
                "features": ["4K", "Без рекламы", "Оффлайн просмотр"]
            }
        }
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError("Название плана не может быть пустым")
        return v.strip()

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Цена не может быть отрицательной")
        return round(v, 2)

class AdminChangeUserRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[str] = None  
    wallet: Optional[Dict[str, Any]] = None
    currentSubscription: Optional[Dict[str, Any]] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None and len(v.strip()) < 1:
            raise ValueError("Username cannot be empty")
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None:
            try:
                from pydantic import EmailStr
                class EmailCheck(BaseModel):
                    email: EmailStr
                EmailCheck(email=v)
            except ValueError:
                raise ValueError("Invalid email format")
        return v

    @field_validator('wallet')
    @classmethod
    def validate_wallet(cls, v):
        if v is not None:
            if 'balance' in v:
                try:
                    v['balance'] = float(v['balance'])
                except (TypeError, ValueError):
                    raise ValueError("Wallet balance must be a number")
        return v

    @field_validator('currentSubscription')
    @classmethod
    def validate_subscription(cls, v):
        if v is not None:
            if 'planId' in v and v['planId']:
                try:
                    v['planId'] = PydanticObjectId(v['planId'])
                except:
                    raise ValueError("Invalid planId format")
            
            if 'endDate' in v and v['endDate']:
                try:
                    if isinstance(v['endDate'], str):
                        v['endDate'] = datetime.fromisoformat(v['endDate'].replace("Z", "+00:00"))
                except ValueError:
                    raise ValueError("Invalid endDate format")
        return v
