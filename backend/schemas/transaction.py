from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import Field, BaseModel, ConfigDict, field_validator
from beanie import Document, PydanticObjectId
from pymongo import IndexModel





class TransactionResponse(BaseModel):
    id: str = Field(alias="_id")
    userId: PydanticObjectId 
    amount: float
    type: str
    status: str
    description: str
    paymentMethod: Optional[str]
    currency: str
    metadata: Optional[Dict[str, Any]]
    date: datetime 
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={object: str, datetime: lambda v: v.isoformat()}
    )
 