from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import Field, ConfigDict, field_validator
from beanie import Document, PydanticObjectId
from pymongo import IndexModel


class Transaction(Document):
    userId: PydanticObjectId
    amount: float = Field(...)
    type: str
    status: str = "pending"
    description: str = ""
    paymentMethod: Optional[str] = None
    currency: str = "RUB"
    metadata: Optional[Dict[str, Any]] = None
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True, json_encoders={PydanticObjectId: str}
    )

    @field_validator("amount")
    @classmethod
    def amount_cannot_be_zero(cls, v):
        if v == 0:
            raise ValueError("Amount cannot be zero")
        return v

    class Settings:
        name = "transactions"
        indexes = [
            IndexModel([("userId", 1)], name="userId_1", background=True),
            IndexModel(
                [("userId", 1), ("createdAt", -1)],
                name="userId_1_createdAt_-1",
                background=True,
            ),
            IndexModel(
                [("type", 1), ("status", 1)], name="type_1_status_1", background=True
            ),
            IndexModel([("date", 1)], name="date_1", background=True),
        ]
        use_state_management = True

    async def before_save(self):
        if self.id is None or (
            self.id is not None and self.get_original_state() is None
        ):
            if self.createdAt is None:
                self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)
