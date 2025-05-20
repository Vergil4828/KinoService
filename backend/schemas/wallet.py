from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import Field, BaseModel, ConfigDict
from beanie import PydanticObjectId




class DepositWalletRequest(BaseModel):
    amount: float = Field(gt=0)
    paymentMethod: str = 'manual'

class WithdrawWalletRequest(BaseModel):
    amount: float = Field(gt=0)
    description: Optional[str] = ''
