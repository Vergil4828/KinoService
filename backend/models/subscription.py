from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import Field, BaseModel, ConfigDict, field_validator
from beanie import Document, PydanticObjectId
from pymongo import IndexModel


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

