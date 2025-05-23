import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status, Depends
from beanie.odm.fields import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClientSession
from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.models.transaction import Transaction
from backend.models.subscription import SubscriptionPlan, SubscriptionHistory
from backend.models.embedded.subscription import CurrentSubscriptionEmbedded
from backend.core.database import get_motor_client
from backend.core.config import logger 
from backend.schemas.subscription import ( 
    SubscriptionPlanResponse,
    PurchaseSubscriptionRequest,
    PurchaseSubscriptionResponse,
    SubscriptionHistoryResponse,
)
from backend.schemas.transaction import TransactionResponse 
from backend.models.embedded.subscription import CurrentSubscriptionEmbedded


class SubscriptionService:
    @staticmethod
    async def get_all_plans() -> List[SubscriptionPlanResponse]:
        """
        **Метод для получения всех тарифных планов.**
        Возвращает список всех доступных тарифных планов.
        **Возвращает:**
        - `plans`: Список тарифных планов с их данными.
        """
        try:
            plans = await SubscriptionPlan.find().sort("price").to_list()

            response = []
            for plan in plans:
                plan_dict = plan.model_dump(by_alias=True)
                plan_dict["_id"] = str(plan_dict["_id"])
                response.append(SubscriptionPlanResponse(**plan_dict))

            return response

        except Exception as err:
            logger.error(f'Ошибка при получении списка тарифных планов: {err}', exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка сервера при получении тарифных планов'
            )
    
    @staticmethod
    async def get_plan_by_id(planId: PydanticObjectId) -> SubscriptionPlanResponse:
        """
        **Метод для получения тарифного плана по ID.**
        Принимает ID тарифного плана и возвращает его данные.
        **Параметры:**
        - `planId`: ID тарифного плана.
        **Возвращает:**
        - `plan`: Объект тарифного плана с его данными.
        """
        try:
            plan = await SubscriptionPlan.get(planId)
            if not plan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тарифный план не найден")

            plan_data_dict = plan.model_dump(by_alias=True)
            plan_data_dict['_id'] = str(plan_data_dict['_id'])
            plan_response_instance = SubscriptionPlanResponse(**plan_data_dict)
            return plan_response_instance


        except Exception as err:
            logger.error(f'Ошибка при получении тарифного плана по ID {planId}: {err}', exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Ошибка сервера при получении тарифного плана')

    @staticmethod
    async def purchase_subscription(
        request_data: PurchaseSubscriptionRequest,
        current_user: User = Depends(get_current_user)
    ) -> PurchaseSubscriptionResponse:
        
        """
        **Метод для покупки подписки.**
        Принимает данные о подписке и текущем пользователе.
        **Параметры:**
        - `request_data`: Данные о подписке (ID плана и другие параметры).
        - `current_user`: Текущий пользователь.
        **Возвращает:**
        - `subscription`: Объект подписки с ее данными.
        """
        try:
            client = get_motor_client()
        except RuntimeError as e:
            logger.error(f"MongoDB client not initialized for purchase_subscription: {e}", exc_info=False)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not ready.")

        async with await client.start_session() as session:
            try:
                async with session.start_transaction():
                    logger.debug(f"purchase_subscription: Поиск пользователя с ID {current_user.id} и плана с ID {request_data.planId} в БД.")
                    user = await User.get(current_user.id, session=session)
                    plan = await SubscriptionPlan.get(request_data.planId, session=session)

                    if not user:
                        logger.error(f"purchase_subscription: Пользователь с ID {current_user.id} не найден во время транзакции. Откат.")
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
                    if not plan:
                        logger.error(f"purchase_subscription: План с ID {request_data.planId} не найден во время транзакции. Откат.")
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

                    logger.debug(f"purchase_subscription: Пользователь и план найдены. Баланс пользователя: {user.wallet.balance}, Цена плана: {plan.price}")

                    now = datetime.now(timezone.utc)
                    transaction: Optional[Transaction] = None
                    response_transaction: Optional[TransactionResponse] = None
                    subscription_history: Optional[SubscriptionHistory] = None

                    is_free_plan = plan.price == 0
                    renewal_days = plan.renewalPeriod if plan.renewalPeriod is not None else 30
                    end_date = None if is_free_plan else (now + timedelta(days=renewal_days))
                    auto_renew = not is_free_plan
                    admin_note = "Бесплатный план" if is_free_plan else "Покупка через баланс"

                    if not is_free_plan:

                        if user.wallet.balance < plan.price:
                            logger.warning(f"purchase_subscription: Недостаточно средств для пользователя {user.id}. Баланс: {user.wallet.balance}, Цена плана: {plan.price}. Требуется оплата.")
                            return PurchaseSubscriptionResponse(
                                success=False,
                                paymentRequired=True,
                                requiredAmount=plan.price - user.wallet.balance,
                                newBalance=user.wallet.balance
                            )

                        logger.debug(f"purchase_subscription: Создание транзакции для пользователя {user.id}. Сумма: -{plan.price}")
                        transaction = Transaction(
                            userId=user.id,
                            amount=-plan.price,
                            type='subscription',
                            status='completed',
                            description=f"Оплата подписки {plan.name}",
                            paymentMethod='balance',
                            currency='RUB',
                            metadata={
                                "planId": str(plan.id),
                                "planName": plan.name,
                                "type": "subscription_payment"
                            },
                            date=now,
                            createdAt=now,
                            updatedAt=now
                        )
                        await transaction.insert(session=session)
                        logger.debug(f"purchase_subscription: Транзакция {transaction.id} успешно создана.")

                        user.wallet.balance -= plan.price
                        user.wallet.transactionIds.append(transaction.id)
                        logger.debug(f"purchase_subscription: Баланс пользователя {user.id} обновлен до {user.wallet.balance}.")

                        response_transaction = TransactionResponse(
                            id=str(transaction.id),
                            userId=str(user.id),
                            amount=transaction.amount,
                            type=transaction.type,
                            status=transaction.status,
                            description=transaction.description,
                            paymentMethod=transaction.paymentMethod,
                            currency=transaction.currency,
                            metadata=transaction.metadata,
                            date=transaction.date,
                            createdAt=transaction.createdAt,
                            updatedAt=transaction.updatedAt
                        )

                        logger.debug(f"purchase_subscription: Создание записи истории подписки для пользователя {user.id}. Конечная дата: {end_date}")
                        subscription_history = SubscriptionHistory(
                            userId=user.id,
                            planId=plan.id,
                            startDate=now,
                            endDate=end_date,
                            isActive=True,
                            autoRenew=auto_renew,
                            changedByAdmin=False,
                            adminNote=admin_note,
                            createdAt=now,
                            updatedAt=now
                        )
                        await subscription_history.insert(session=session)
                        logger.debug(f"purchase_subscription: Запись истории подписки {subscription_history.id} успешно создана.")

                    user.currentSubscription = CurrentSubscriptionEmbedded(
                        planId=plan.id,
                        startDate=now,
                        endDate=end_date,
                        isActive=True,
                        autoRenew=auto_renew,
                        adminNote=admin_note,
                        plan=SubscriptionPlanResponse(
                            id=str(plan.id),
                            name=plan.name,
                            price=plan.price,
                            renewalPeriod=plan.renewalPeriod,
                            features=plan.features,
                            createdAt=plan.createdAt,
                            updatedAt=plan.updatedAt
                        )
                    )
                    await user.save(session=session)
                    logger.debug(f"purchase_subscription: Текущая подписка пользователя {user.id} обновлена.")

                    response_subscription_history = None
                    if subscription_history:
                        response_subscription_history = SubscriptionHistoryResponse(
                            id=str(subscription_history.id),
                            userId=str(user.id),
                            planId=str(plan.id),
                            startDate=now,
                            endDate=end_date,
                            isActive=True,
                            autoRenew=auto_renew,
                            changedByAdmin=False,
                            adminNote=admin_note,
                            createdAt=now,
                            updatedAt=now,
                            plan=SubscriptionPlanResponse(
                                id=str(plan.id),
                                name=plan.name,
                                price=plan.price,
                                renewalPeriod=plan.renewalPeriod,
                                features=plan.features,
                                createdAt=plan.createdAt,
                                updatedAt=plan.updatedAt
                            )
                        )

                    response = PurchaseSubscriptionResponse(
                        success=True,
                        subscription=response_subscription_history, 
                        newBalance=user.wallet.balance,
                        transaction=response_transaction, 
                        paymentRequired=False,
                        requiredAmount=0
                    )

                    await session.commit_transaction()
                    logger.info(f"purchase_subscription: Транзакция подписки для пользователя {user.id} успешно завершена. Возврат ответа.")
                    return response

            except HTTPException as http_exc:
                if session.in_transaction:
                    await session.abort_transaction()
                    logger.warning(f"purchase_subscription: Транзакция отменена из-за HTTP исключения: {http_exc.detail} (Статус: {http_exc.status_code})")
                raise http_exc
            except Exception as err:
                logger.error(f"purchase_subscription: Неожиданная ошибка при покупке подписки: {str(err)}", exc_info=True)
                if session.in_transaction:
                    await session.abort_transaction()
                    logger.warning("purchase_subscription: Транзакция отменена из-за неожиданной ошибки.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error during subscription purchase"
                )
              
    @staticmethod
    async def get_current_subscription(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
        """
        **Метод для получения текущей подписки пользователя.**
        Принимает текущего пользователя и возвращает его подписку.
        **Параметры:**
        - `current_user`: Текущий пользователь.
        **Возвращает:**
        - `subscription`: Объект подписки с ее данными.
        """
        try:
            user = await User.get(current_user.id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            if not user.currentSubscription or not user.currentSubscription.planId:
                basic_plan = await SubscriptionPlan.find_one(SubscriptionPlan.price == 0)
                if not basic_plan:
                    raise HTTPException(
                        status_code=500,
                        detail="Basic plan not found"
                    )
                
                return {
                    "planId": str(basic_plan.id),
                    "name": basic_plan.name,
                    "startDate": None,
                    "endDate": None,
                    "isActive": True,
                    "autoRenew": False,
                    "plan": {
                        "id": str(basic_plan.id),
                        "name": basic_plan.name,
                        "price": basic_plan.price,
                        "features": basic_plan.features,
                        "renewalPeriod": basic_plan.renewalPeriod
                    }
                }

            plan = await SubscriptionPlan.get(user.currentSubscription.planId)
            if not plan:
                raise HTTPException(
                    status_code=404,
                    detail="Subscription plan not found"
                )

            subscription_data = {
                "planId": str(user.currentSubscription.planId),
                "name": plan.name,
                "startDate": user.currentSubscription.startDate.isoformat() if user.currentSubscription.startDate else None,
                "endDate": user.currentSubscription.endDate.isoformat() if user.currentSubscription.endDate else None,
                "isActive": user.currentSubscription.isActive,
                "autoRenew": user.currentSubscription.autoRenew,
                "plan": {
                    "id": str(plan.id),
                    "name": plan.name,
                    "price": plan.price,
                    "features": plan.features,
                    "renewalPeriod": plan.renewalPeriod
                }
            }

            return subscription_data

        except Exception as err:
            logger.error(f'Error getting current subscription: {err}', exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Error getting current subscription'
            )