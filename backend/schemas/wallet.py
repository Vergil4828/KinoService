from __future__ import annotations
from typing import Optional
from pydantic import Field, BaseModel, field_validator


class DepositWalletRequest(BaseModel):
    amount: float
    paymentMethod: str = "manual"

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if isinstance(v, bool):
            raise ValueError("Сумма должна быть числом, не булевым значением.")
        if v is None:
            raise ValueError("Сумма обязательна для заполнения.")
        if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
            raise ValueError("Сумма должна быть конечным числом.")
        if v < 10:
            raise ValueError("Сумма пополнения должна быть не менее 10.")
        if round(v, 2) != v:
            raise ValueError("Сумма может иметь максимум два знака после запятой.")
        return v


class WithdrawWalletRequest(BaseModel):
    amount: float = Field(gt=0)
    description: Optional[str] = ""
