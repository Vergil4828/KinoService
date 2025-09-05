from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import (
    Field,
    BaseModel,
    ConfigDict,
    field_validator,
    EmailStr,
    ValidationInfo,
)

import re


class UserResponseBase(BaseModel):
    id: str = Field(alias="_id")
    username: str
    email: Optional[str] = None
    avatar: str
    notifications: "NotificationsEmbedded"
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    role: str
    currentSubscription: Optional["CurrentSubscriptionEmbedded"] = None
    wallet: "WalletEmbedded" = Field(default_factory=lambda: WalletEmbedded())
    history: List["SubscriptionHistoryResponse"] = Field(default_factory=list)
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={object: str, datetime: lambda v: v.isoformat()},
    )


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    confirmPassword: str = Field(min_length=8, max_length=72)
    notifications: Optional[NotificationsEmbedded] = Field(
        default_factory=lambda: NotificationsEmbedded()
    )

    @field_validator("username", "password", "confirmPassword", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("username")
    @classmethod
    def validate_username_characters(cls, v: str) -> str:
        """
        Username может содержать только:
        - латинские буквы (a-z, A-Z)
        - цифры (0-9)
        - дефис (-)
        - подчеркивание (_)
        """
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username может содержать только латинские буквы, цифры, \
                дефис (-) и подчеркивание (_)"
            )

        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Username не может начинаться или заканчиваться дефисом")

        if v.startswith("_") or v.endswith("_"):
            raise ValueError(
                "Username не может начинаться или заканчиваться подчеркиванием"
            )

        if "--" in v or "__" in v or "-_" in v or "_-" in v:
            raise ValueError(
                "Username не может содержать последовательные специальные символы"
            )

        return v

    @field_validator("email", mode="after")
    @classmethod
    def validate_email_additional(cls, v: EmailStr) -> EmailStr:

        email_str = str(v)
        local_part = email_str.split("@")[0]
        if local_part.startswith(".") or local_part.endswith("."):
            raise ValueError(
                "Email не может начинаться или заканчиваться точкой в локальной части"
            )

        if ".." in local_part:
            raise ValueError("Email не может содержать последовательные точки")

        if len(local_part) > 64:
            raise ValueError("Локальная часть email не может превышать 64 символа")

        domain = email_str.split("@")[1]
        if len(domain) > 255:
            raise ValueError("Доменная часть email не может превышать 255 символов")

        return v

    @field_validator("confirmPassword")
    @classmethod
    def passwords_match(cls, v: str, info: ValidationInfo) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Пароли не совпадают")
        return v


class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("email", mode="after")
    @classmethod
    def validate_email_additional(cls, v: EmailStr) -> EmailStr:
        email_str = str(v)
        local_part = email_str.split("@")[0]

        if local_part.startswith(".") or local_part.endswith("."):
            raise ValueError(
                "Email не может начинаться или заканчиваться точкой в локальной части"
            )

        if ".." in local_part:
            raise ValueError("Email не может содержать последовательные точки")

        if len(local_part) > 64:
            raise ValueError("Локальная часть email не может превышать 64 символа")

        domain = email_str.split("@")[1]
        if len(domain) > 255:
            raise ValueError("Доменная часть email не может превышать 63 символов")

        return v


class UpdateUserRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    currentPassword: str = Field(min_length=8, max_length=72)
    newPassword: Optional[str] = Field(None, min_length=8, max_length=72)

    @field_validator("username", "currentPassword", "newPassword", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("username")
    @classmethod
    def validate_username_characters(cls, v: Optional[str]) -> Optional[str]:
        """
        Username может содержать только:
        - латинские буквы (a-z, A-Z)
        - цифры (0-9)
        - дефис (-)
        - подчеркивание (_)
        """
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username может содержать только латинские буквы, цифры, \
                дефис (-) и подчеркивание (_)"
            )

        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Username не может начинаться или заканчиваться дефисом")

        if v.startswith("_") or v.endswith("_"):
            raise ValueError(
                "Username не может начинаться или заканчиваться подчеркиванием"
            )

        if "--" in v or "__" in v or "-_" in v or "_-" in v:
            raise ValueError(
                "Username не может содержать последовательные специальные символы"
            )
        return v

    @field_validator("email", mode="after")
    @classmethod
    def validate_email_additional(cls, v: EmailStr) -> EmailStr:

        email_str = str(v)
        local_part = email_str.split("@")[0]
        if local_part.startswith(".") or local_part.endswith("."):
            raise ValueError(
                "Email не может начинаться или заканчиваться точкой в локальной части"
            )

        if ".." in local_part:
            raise ValueError("Email не может содержать последовательные точки")

        if len(local_part) > 64:
            raise ValueError("Локальная часть email не может превышать 64 символа")

        domain = email_str.split("@")[1]
        if len(domain) > 255:
            raise ValueError("Доменная часть email не может превышать 63 символа")

        return v


try:
    from backend.models.embedded.notification import NotificationsEmbedded
    from backend.models.embedded.subscription import CurrentSubscriptionEmbedded
    from backend.models.embedded.wallet import WalletEmbedded
    from backend.schemas.subscription import (
        SubscriptionHistoryResponse,
        SubscriptionPlanResponse,
    )

    UserResponseBase.model_rebuild()
    CreateUserRequest.model_rebuild()
    UpdateUserRequest.model_rebuild()
    LoginUserRequest.model_rebuild()
except ImportError as e:
    import logging

    logging.warning(f"Could not update forward refs: {e}")
