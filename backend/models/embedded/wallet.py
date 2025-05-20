from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import Field, BaseModel, ConfigDict
from beanie import PydanticObjectId

from backend.schemas.transaction import TransactionResponse


class WalletEmbedded(BaseModel):
    balance: float = Field(default=0.0, ge=0)
    transactionIds: List[PydanticObjectId] = []
    transactions: List['TransactionResponse'] = Field(default_factory=list)

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat() if v else None}
    )