from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import Field, BaseModel, field_validator
from fastapi import HTTPException, status




class DepositWalletRequest(BaseModel):
    amount: float
    paymentMethod: str = 'manual'

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if isinstance(v, bool):
            raise ValueError('Сумма должна быть числом, не булевым значением.')
        if v is None:
            raise ValueError('Сумма обязательна для заполнения.')
        if v < 10:
            raise ValueError('Сумма пополнения должна быть не менее 10.')
        if round(v, 2) != v:
            raise ValueError('Сумма может иметь максимум два знака после запятой.')
        return v

class WithdrawWalletRequest(BaseModel):
    amount: float = Field(gt=0)
    description: Optional[str] = ''
