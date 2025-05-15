from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import Field, BaseModel, ConfigDict, field_validator
from beanie import Document, PydanticObjectId, IndexModel

from .transaction import TransactionResponse


class SubscriptionPlan(Document):
    name: str = Field(..., unique=True)
    price: float = Field(ge=0)
    renewalPeriod: int = Field(default=30, ge=0)
    features: List[str] = []
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Settings:
        name = "subscriptionplans"
        use_state_management = True
        use_revision = True
        indexes = [
            IndexModel([("name", 1)], unique=True),
        ]

    async def before_save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)


class SubscriptionPlanResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    price: float
    renewalPeriod: int
    features: List[str]
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() if v else None},
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "Премиум",
                "price": 999,
                "renewalPeriod": 30,
                "features": ["4K", "Без рекламы"],
                "createdAt": "2023-01-01T00:00:00Z",
                "updatedAt": "2023-01-02T00:00:00Z"
            }
        }
    )

class SubscriptionHistory(Document):
    userId: PydanticObjectId
    planId: PydanticObjectId
    startDate: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    endDate: Optional[datetime] = None  
    isActive: bool = True
    autoRenew: bool = True
    changedByAdmin: bool = False
    adminNote: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Settings:
        name = "subscriptionhistories"
        indexes = [
            IndexModel([("userId", 1)], name="userId_1", background=True),
            IndexModel([("planId", 1)], name="planId_1", background=True),
        ]
        use_state_management = True

    async def before_save(self):
        if not self.createdAt:
            self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)

class SubscriptionHistoryEmbedded(BaseModel):
    planId: Optional[PydanticObjectId] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None  
    isActive: bool = True
    changedByAdmin: bool = False
    adminNote: Optional[str] = None
    plan: Optional['SubscriptionPlanResponse'] = None

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat() if v else None}
    )
    
class CurrentSubscriptionEmbedded(BaseModel):
    planId: Optional[PydanticObjectId] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    isActive: bool = True
    autoRenew: bool = True
    adminNote: Optional[str] = None
    plan: Optional[Union[Dict[str, Any], 'SubscriptionPlanResponse']] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            PydanticObjectId: lambda v: str(v) if v else None
        }
    )

    @field_validator('plan', mode='before')
    @classmethod
    def convert_plan_to_dict(cls, v):
        if v is None:
            return None
        if isinstance(v, SubscriptionPlanResponse):
            return v.model_dump(by_alias=True)
        return v


class SubscriptionHistoryResponse(BaseModel):
    id: str = Field(alias="_id")
    userId: PydanticObjectId
    planId: PydanticObjectId
    startDate: datetime
    endDate: Optional[datetime] = None  
    isActive: bool
    autoRenew: bool
    changedByAdmin: bool
    adminNote: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    plan: Optional[SubscriptionPlanResponse] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() if v else None}
    )


class PurchaseSubscriptionRequest(BaseModel):
    planId: PydanticObjectId


class PurchaseSubscriptionResponse(BaseModel):
    success: bool
    subscription: Optional[SubscriptionHistoryResponse] = None
    newBalance: Optional[float] = None
    transaction: Optional[TransactionResponse] = None
    paymentRequired: bool = False
    requiredAmount: float = 0

    model_config = ConfigDict(
        json_encoders={object: str, datetime: lambda v: v.isoformat()},
        populate_by_name=True 
    )
