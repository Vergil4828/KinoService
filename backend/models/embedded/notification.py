from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import Field, BaseModel, ConfigDict, field_validator
from beanie import Document, PydanticObjectId
from pymongo import IndexModel





class NotificationsEmbedded(BaseModel):
    email: bool = False
    push: bool = False
    newsletter: bool = False

