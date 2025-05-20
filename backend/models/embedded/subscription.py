from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union, TYPE_CHECKING, ForwardRef
from pydantic import Field, BaseModel, ConfigDict, field_validator
from beanie import Document, PydanticObjectId
from pymongo import IndexModel

from backend.schemas.subscription import SubscriptionPlanResponse


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
