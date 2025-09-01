from datetime import datetime, timezone  # Для установки updated_at и работы с датами
from beanie import PydanticObjectId  # Для работы с ObjectId MongoDB
from fastapi import (
    HTTPException,
    status,
    Request,
    Depends,
)  # HTTPException и status для обработки ошибок, Request для доступа к заголовкам, Depends для внедрения зависимостей
from pymongo.errors import (
    DuplicateKeyError,
)  # Для перехвата ошибки дублирования ключа при создании плана

from backend.models.user import User  # Модель пользователя (для admin_user)
from backend.models.subscription import SubscriptionPlan  # Модель тарифного плана
from backend.schemas.admin import (
    AdminChangePlanRequest,
)  # Модель запроса для изменения/создания плана
from backend.core.dependencies import (
    log_admin_action,
)  # Ваша утилита для логирования действий администратора
from backend.core.database import (
    get_motor_client,
)  # Ваша функция для получения клиента Motor (для транзакций)
from backend.core.dependencies import (
    get_admin_user,
)  # Ваша зависимость для получения администратора
from backend.core.config import logger  # Логгер для записи ошибок и информации


class AdminPlanService:
    @staticmethod
    async def admin_change_plan(
        planId: PydanticObjectId,
        request_data: AdminChangePlanRequest,
        request: Request,
        admin_user: User = Depends(get_admin_user),
    ):
        """
        **Метод для изменения существующего тарифного плана.**
        Принимает ID тарифного плана и новые данные о тарифном плане.
        Изменяет данные в системе.
        **Возвращает:**
        - `plan`: Объект измененного тарифного плана.
        - `message`: Сообщение об успешном изменении.
        """
        try:
            client = get_motor_client()
        except RuntimeError as e:
            logger.error(
                f"MongoDB client not initialized for admin_change_plan: {e}",
                exc_info=False,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        async with await client.start_session() as session:
            async with session.start_transaction():
                try:
                    plan = await SubscriptionPlan.get(planId, session=session)
                    if not plan:
                        raise HTTPException(
                            status_code=404, detail="Subscription plan not found"
                        )

                    update_fields = {}
                    changes = {}

                    if request_data.name is not None and request_data.name != plan.name:
                        if len(request_data.name) < 1:
                            raise HTTPException(
                                status_code=400, detail="Plan name too short"
                            )
                        update_fields["name"] = request_data.name
                        changes["name"] = {"old": plan.name, "new": request_data.name}

                    if (
                        request_data.price is not None
                        and request_data.price != plan.price
                    ):
                        if request_data.price < 0:
                            raise HTTPException(
                                status_code=400, detail="Price cannot be negative"
                            )
                        update_fields["price"] = request_data.price
                        changes["price"] = {
                            "old": plan.price,
                            "new": request_data.price,
                        }

                    if (
                        request_data.renewalPeriod is not None
                        and request_data.renewalPeriod != plan.renewalPeriod
                    ):
                        if request_data.renewalPeriod < 1:
                            raise HTTPException(
                                status_code=400,
                                detail="Renewal period must be at least 1 day",
                            )
                        update_fields["renewalPeriod"] = request_data.renewalPeriod
                        changes["renewalPeriod"] = {
                            "old": plan.renewalPeriod,
                            "new": request_data.renewalPeriod,
                        }

                    if (
                        request_data.features is not None
                        and request_data.features != plan.features
                    ):
                        if not isinstance(request_data.features, list):
                            raise HTTPException(
                                status_code=400, detail="Features must be a list"
                            )
                        update_fields["features"] = request_data.features
                        changes["features"] = {
                            "old": plan.features,
                            "new": request_data.features,
                        }

                    if update_fields:
                        update_fields["updatedAt"] = datetime.now(timezone.utc)

                        await SubscriptionPlan.find_one({"_id": planId}).update(
                            {"$set": update_fields}, session=session
                        )

                        updated_plan = await SubscriptionPlan.get(
                            planId, session=session
                        )

                        await log_admin_action(
                            admin_user,
                            request,
                            "update",
                            "SubscriptionPlan",
                            planId,
                            changes,
                            f"Admin {admin_user.email} updated subscription plan {planId}",
                        )

                    await session.commit_transaction()

                    plan_data = updated_plan.model_dump(by_alias=True)
                    plan_data["_id"] = str(plan_data["_id"])

                    return {"success": True, "plan": plan_data}

                except HTTPException as http_exc:
                    await session.abort_transaction()
                    raise http_exc
                except DuplicateKeyError:
                    await session.abort_transaction()
                    raise HTTPException(
                        status_code=400,
                        detail="Subscription plan with this name already exists",
                    )
                except Exception as e:
                    await session.abort_transaction()
                    logger.error(
                        f"Error updating subscription plan: {str(e)}", exc_info=True
                    )
                    raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    async def admin_create_plan(
        request_data: AdminChangePlanRequest,
        request: Request,
        admin_user: User = Depends(get_admin_user),
    ):
        """
        **Метод для создания нового тарифного плана.**
        Принимает данные о тарифном плане и создает новый план в системе.
        **Возвращает:**
        - `plan`: Объект созданного тарифного плана.
        - `message`: Сообщение об успешном создании.
        """
        try:

            client = get_motor_client()
        except RuntimeError as e:
            logger.error(
                f"MongoDB client not initialized for admin_create_plan: {e}",
                exc_info=False,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        try:
            if not request_data.name:
                raise HTTPException(status_code=400, detail="Plan name is required")
            if request_data.price is None:
                raise HTTPException(status_code=400, detail="Price is required")
            if request_data.renewalPeriod is None:
                raise HTTPException(
                    status_code=400, detail="Renewal period is required"
                )

            existing_plan = await SubscriptionPlan.find_one(
                SubscriptionPlan.name == request_data.name
            )
            if existing_plan:
                raise HTTPException(
                    status_code=400, detail="Plan with this name already exists"
                )

            new_plan = SubscriptionPlan(
                name=request_data.name,
                price=request_data.price,
                renewalPeriod=request_data.renewalPeriod,
                features=request_data.features or [],
            )

            await new_plan.insert()

            await log_admin_action(
                admin_user,
                request,
                "create",
                "SubscriptionPlan",
                new_plan.id,
                None,
                f"Admin {admin_user.email} created new subscription plan: {request_data.name}",
            )

            plan_data = new_plan.model_dump(by_alias=True)
            plan_data["_id"] = str(plan_data["_id"])

            return {
                "success": True,
                "message": "Тарифный план успешно создан",
                "plan": plan_data,
            }

        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Error creating subscription plan: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    async def admin_delete_plan(
        planId: PydanticObjectId,
        request: Request,
        admin_user: User = Depends(get_admin_user),
    ):
        """
        **Метод для удаления тарифного плана.**
        Принимает ID тарифного плана и удаляет его из системы.
        **Возвращает:**
        - `success`: True, если удаление прошло успешно.
        - `message`: Сообщение об успешном удалении.
        """
        try:

            client = get_motor_client()
        except RuntimeError as e:
            logger.error(
                f"MongoDB client not initialized for admin_delete_plan: {e}",
                exc_info=False,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        async with await client.start_session() as session:
            async with session.start_transaction():
                try:
                    plan_to_delete = await SubscriptionPlan.get(planId, session=session)
                    if not plan_to_delete:
                        await session.abort_transaction()
                        raise HTTPException(
                            status_code=404, detail="Subscription plan not found"
                        )

                    users_with_plan = await User.find_one(
                        {"currentSubscription.planId": planId}, session=session
                    )

                    if users_with_plan:
                        await session.abort_transaction()
                        raise HTTPException(
                            status_code=400,
                            detail="Cannot delete plan - it's currently used by users",
                        )

                    await plan_to_delete.delete(session=session)

                    await log_admin_action(
                        admin_user,
                        request,
                        "delete",
                        "SubscriptionPlan",
                        planId,
                        None,
                        f"Admin {admin_user.email} deleted subscription plan: {plan_to_delete.name}",
                    )

                    await session.commit_transaction()

                    return {"success": True, "message": "Тарифный план успешно удален"}

                except HTTPException as http_exc:
                    await session.abort_transaction()
                    raise http_exc
                except Exception as e:
                    await session.abort_transaction()
                    logger.error(
                        f"Error deleting subscription plan: {str(e)}", exc_info=True
                    )
                    raise HTTPException(status_code=500, detail="Internal server error")
