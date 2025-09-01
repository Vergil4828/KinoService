from __future__ import annotations
from datetime import datetime
from typing import List
from pydantic import Field, BaseModel, ConfigDict
from beanie import PydanticObjectId


class WalletEmbedded(BaseModel):
    balance: float = Field(default=0.0, ge=0)
    transactionIds: List[PydanticObjectId] = []
    model_config = ConfigDict(
        arbitrary_types_allowed=True, 
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            PydanticObjectId: str
        }
    )