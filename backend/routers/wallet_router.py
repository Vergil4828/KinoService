from fastapi import APIRouter, Depends
from typing import Dict, Any
from backend.core.dependencies import get_current_user
from backend.models.user import User

from backend.services.wallet_service import WalletService

from backend.schemas.wallet import DepositWalletRequest, WithdrawWalletRequest

router = APIRouter(prefix="/api", tags=["Wallet"])


@router.get("/wallet")
async def get_wallet_data_route(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    **Эндпоинт для получения данных о кошельке пользователя.**
    Возвращает информацию о текущем кошельке пользователя.
    **Возвращает:**
    - `wallet`: Объект кошелька с его данными.
    """
    return await WalletService.get_wallet_data(current_user)


@router.post("/wallet/deposit")
async def deposit_wallet_route(
    request_data: DepositWalletRequest, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    **Эндпоинт для пополнения кошелька пользователя.**
    Принимает данные о пополнении кошелька и текущем пользователе.
    **Параметры:**
    - `request_data`: Данные о пополнении (сумма и другие параметры).
    - `current_user`: Текущий пользователь.
    **Возвращает:**
    - `transaction`: Объект транзакции с ее данными.
    """
    return await WalletService.deposit_wallet(request_data, current_user)


@router.post("/wallet/withdraw")
async def withdraw_wallet_route(
    request_data: WithdrawWalletRequest, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    **Эндпоинт для вывода средств из кошелька пользователя.**
    Принимает данные о выводе средств и текущем пользователе.
    **Параметры:**
    - `request_data`: Данные о выводе (сумма и другие параметры).
    - `current_user`: Текущий пользователь.
    **Возвращает:**
    - `transaction`: Объект транзакции с ее данными.
    """
    return await WalletService.withdraw_wallet(request_data, current_user)
