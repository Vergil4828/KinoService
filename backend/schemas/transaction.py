from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import Field, BaseModel, ConfigDict, field_validator
from beanie import Document, PydanticObjectId
from pymongo import IndexModel
from bson import ObjectId




class TransactionResponse(BaseModel):
    id: str = Field(alias="_id")  
    userId: str  
    amount: float
    type: str
    status: str
    description: str
    paymentMethod: Optional[str] = None
    currency: str
    metadata: Optional[Dict[str, Any]] = None
    date: datetime 
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

    @field_validator('id', 'userId')
    def validate_objectid(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError(f"Invalid ObjectId: {v}")
        return v