import logging
from typing import List

from fastapi import APIRouter, HTTPException, status, Depends

from backend.models.user import User
from backend.core.dependencies import get_current_user
from backend.core.config import logger

from backend.services.subscription_service import SubscriptionService 
from backend.schemas.subscription import (
    SubscriptionPlanResponse,
    PurchaseSubscriptionRequest,
    PurchaseSubscriptionResponse
)
from backend.models.embedded.subscription import CurrentSubscriptionEmbedded


router = APIRouter(prefix="/api", tags=["Subscriptions"])

@router.get('/plans', response_model=List[SubscriptionPlanResponse])
async def get_all_plans_route():
    """
    **Эндпоинт для получения всех тарифных планов.**
    Возвращает список всех доступных тарифных планов.
    **Возвращает:**
    - `plans`: Список тарифных планов с их данными.
    """
    return await SubscriptionService.get_all_plans()

@router.get('/plans/{planId}', response_model=SubscriptionPlanResponse)
async def get_plan_by_id_route(planId: str):
    """
    **Эндпоинт для получения тарифного плана по ID.**
    Принимает ID тарифного плана и возвращает его данные.
    **Параметры:**
    - `planId`: ID тарифного плана.
    **Возвращает:**
    - `plan`: Объект тарифного плана с его данными.
    """
    return await SubscriptionService.get_plan_by_id(planId)

@router.post('/subscriptions/purchase', response_model=PurchaseSubscriptionResponse)
async def purchase_subscription_route(
    request_data: PurchaseSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    **Эндпоинт для покупки подписки.**
    Принимает данные о подписке и текущем пользователе.
    **Параметры:**
    - `request_data`: Данные о подписке (ID плана и другие параметры).
    - `current_user`: Текущий пользователь.
    **Возвращает:**
    - `subscription`: Объект подписки с ее данными.
    """
    return await SubscriptionService.purchase_subscription(request_data, current_user)

@router.get('/subscriptions/current', response_model=CurrentSubscriptionEmbedded)
async def get_current_subscription_route(current_user: User = Depends(get_current_user)):
    """
    **Эндпоинт для получения текущей подписки пользователя.**
    Возвращает данные о текущей подписке пользователя.
    **Параметры:**
    - `current_user`: Текущий пользователь.
    **Возвращает:**
    - `subscription`: Объект текущей подписки с ее данными.
    """
    return await SubscriptionService.get_current_subscription(current_user)
