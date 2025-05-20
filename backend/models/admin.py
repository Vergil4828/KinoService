from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import Field, BaseModel, ConfigDict
from beanie import Document, PydanticObjectId
from pymongo import IndexModel
from pydantic import field_validator

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import UserResponseBase

class AdminAction(Document):
    adminId: PydanticObjectId 
    actionType: str
    targetModel: str
    targetId: Optional[PydanticObjectId] = None
    changes: Optional[Dict[str, Any]] = None
    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None
    additionalInfo: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Settings:
        name = "adminactions"
        indexes = [
            IndexModel([("adminId", 1)], name="adminId_1", background=True),
            IndexModel([("targetModel", 1), ("targetId", 1)], name="targetModel_1_targetId_1", background=True),
            IndexModel([("createdAt", -1)], name="createdAt_-1", background=True),
        ]
        use_state_management = True

    async def before_save(self):
        if self.id is None or (self.id is not None and self.get_original_state() is None):
             if self.createdAt is None:
                  self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)

