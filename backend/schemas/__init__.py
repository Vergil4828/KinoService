# Основные схемы
from __future__ import annotations
from .admin import AdminActionResponse, AdminChangePlanRequest, AdminChangeUserRequest
from .subscription import (
    SubscriptionPlanResponse,
    SubscriptionHistoryResponse,
    PurchaseSubscriptionRequest,
    PurchaseSubscriptionResponse
)
from .transaction import TransactionResponse
from .user import UserResponseBase, CreateUserRequest, LoginUserRequest, UpdateUserRequest
from .token import RefreshTokenRequest
from .wallet import DepositWalletRequest, WithdrawWalletRequest

__all__ = [
    'AdminActionResponse',
    'AdminChangePlanRequest',
    'AdminChangeUserRequest',
    'SubscriptionPlanResponse',
    'SubscriptionHistoryResponse',
    'PurchaseSubscriptionRequest',
    'PurchaseSubscriptionResponse',
    'TransactionResponse',
    'UserResponseBase',
    'CreateUserRequest',
    'LoginUserRequest',
    'UpdateUserRequest',
    'RefreshTokenRequest',
    'DepositWalletRequest',
    'WithdrawWalletRequest'
]