from __future__ import annotations
from pydantic import BaseModel


class NotificationsEmbedded(BaseModel):
    email: bool = False
    push: bool = False
    newsletter: bool = False
