from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import Field, BaseModel, ConfigDict
from beanie import PydanticObjectId

from .transaction import TransactionResponse


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
                "updatedAt": "2023-01-02T00:00:00Z",
            }
        },
    )


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
        json_encoders={datetime: lambda v: v.isoformat() if v else None},
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
        populate_by_name=True,
    )
