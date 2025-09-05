import math
from beanie import PydanticObjectId, exceptions as beanie_exceptions
from fastapi import HTTPException, status, Query, Request
from pydantic import BaseModel, EmailStr, ValidationError

from backend.models.user import User
from backend.models.subscription import SubscriptionPlan
from backend.schemas.admin import AdminChangeUserRequest
from backend.core.dependencies import log_admin_action
from backend.core.database import get_motor_client
from backend.core.config import logger


class AdminUserService:
    @staticmethod
    async def get_admin_users(
        page: int = Query(1, ge=1),
        limit: int = Query(25, ge=0),
        search: str = Query("", alias="search"),
    ):
        """
        **Метод для получения списка пользователей.**
        Возвращает список пользователей с возможностью фильтрации по email или username.
        **Параметры:**
        - `page`: Номер страницы (по умолчанию 1).
        - `limit`: Количество пользователей на странице (по умолчанию 25, 0 - все).
        - `search`: Строка для поиска по email или username (по умолчанию пустая строка).
        **Возвращает:**
        - `success`: Успех операции.
        - `users`: Список пользователей с их данными.
        - `total`: Общее количество пользователей.
        - `page`: Номер текущей страницы.
        - `pages`: Общее количество страниц.
        """

        try:
            skip = (page - 1) * limit

            query = {}
            if search:
                query["$or"] = [
                    {"email": {"$regex": search, "$options": "i"}},
                    {"username": {"$regex": search, "$options": "i"}},
                ]

            total = await User.find(query).count()

            pipeline = [
                {"$match": query},
            ]
            if limit > 0:
                pipeline.append({"$skip": skip})
                pipeline.append({"$limit": limit})

            pipeline.extend(
                [
                    {
                        "$lookup": {
                            "from": "subscriptionplans",
                            "localField": "currentSubscription.planId",
                            "foreignField": "_id",
                            "as": "currentSubscription.plan",
                        }
                    },
                    {
                        "$addFields": {
                            "currentSubscription.plan": {
                                "$cond": {
                                    "if": {"$isArray": "$currentSubscription.plan"},
                                    "then": {
                                        "$arrayElemAt": ["$currentSubscription.plan", 0]
                                    },
                                    "else": None,
                                }
                            },
                            "wallet": {
                                "$ifNull": [
                                    "$wallet",
                                    {"balance": 0, "transactions": []},
                                ]
                            },
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "username": 1,
                            "email": 1,
                            "currentSubscription": 1,
                            "wallet.balance": 1,
                            "createdAt": 1,
                        }
                    },
                ]
            )

            users_cursor = User.aggregate(pipeline)
            users_list = await users_cursor.to_list()

            populated_users = []
            for user in users_list:
                user_data = {
                    "_id": str(user["_id"]),
                    "username": user.get("username"),
                    "email": user.get("email"),
                    "wallet": {"balance": user.get("wallet", {}).get("balance", 0)},
                    "createdAt": (
                        user.get("createdAt").isoformat()
                        if user.get("createdAt")
                        else None
                    ),
                    "currentSubscription": None,
                }

                if user.get("currentSubscription"):
                    sub_data = user["currentSubscription"]
                    plan_id_str = (
                        str(sub_data["planId"]) if sub_data.get("planId") else None
                    )

                    user_data["currentSubscription"] = {
                        "planId": plan_id_str,
                        "startDate": (
                            sub_data.get("startDate").isoformat()
                            if sub_data.get("startDate")
                            else None
                        ),
                        "endDate": (
                            sub_data.get("endDate").isoformat()
                            if sub_data.get("endDate")
                            else None
                        ),
                        "isActive": sub_data.get("isActive", False),
                        "autoRenew": sub_data.get("autoRenew", False),
                        "adminNote": sub_data.get("adminNote"),
                        "plan": None,
                    }

                    if sub_data.get("plan"):
                        user_data["currentSubscription"]["plan"] = {
                            "_id": str(sub_data["plan"]["_id"]),
                            "name": sub_data["plan"].get("name"),
                            "price": sub_data["plan"].get("price"),
                            "features": sub_data["plan"].get("features", []),
                        }

                populated_users.append(user_data)

            pages = math.ceil(total / limit) if limit > 0 else (1 if total > 0 else 0)

            return {
                "success": True,
                "users": populated_users,
                "total": total,
                "page": page,
                "pages": pages,
            }

        except Exception as err:
            logger.error(
                f"Ошибка при получении списка пользователей: {err}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка сервера при получении списка пользователей",
            )

    @staticmethod
    async def admin_change_user(
        userId: PydanticObjectId,
        request_data: AdminChangeUserRequest,
        request: Request,
        admin_user: User,
    ):
        """
        **Метод для изменения данных пользователя администратором.**
        Принимает ID пользователя и данные для обновления.
        **Параметры:**
        - `userId`: ID пользователя, данные которого нужно изменить.
        - `request_data`: Данные для обновления (username, email, wallet, currentSubscription).
        **Возвращает:**
        - `success`: Успех операции.
        - `user`: Обновленные данные пользователя.
        """
        try:
            client = get_motor_client()
        except RuntimeError as e:
            logger.error(
                f"MongoDB client not initialized for admin_change_user: {e}",
                exc_info=False,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        async with await client.start_session() as session:
            async with session.start_transaction():
                try:
                    user = await User.get(userId, session=session)
                    if not user:
                        raise HTTPException(status_code=404, detail="User not found")
                    update_fields = {}
                    changes = {}

                    if (
                        request_data.username is not None
                        and request_data.username != user.username
                    ):
                        if len(request_data.username) < 1:
                            raise HTTPException(
                                status_code=400, detail="Username too short"
                            )
                        update_fields["username"] = request_data.username
                        changes["username"] = {
                            "old": user.username,
                            "new": request_data.username,
                        }

                    if (
                        request_data.email is not None
                        and request_data.email != user.email
                    ):
                        try:

                            class EmailCheck(BaseModel):
                                email: EmailStr

                            EmailCheck(email=request_data.email)

                            existing_user = await User.find_one(
                                {"email": request_data.email, "_id": {"$ne": userId}},
                                session=session,
                            )
                            if existing_user:
                                raise HTTPException(
                                    status_code=400, detail="Email already in use"
                                )

                            update_fields["email"] = request_data.email
                            changes["email"] = {
                                "old": user.email,
                                "new": request_data.email,
                            }
                        except ValidationError:
                            raise HTTPException(
                                status_code=400, detail="Invalid email format"
                            )
                        except Exception as e:
                            logger.error(f"Error validating email: {e}", exc_info=True)
                            raise HTTPException(
                                status_code=500,
                                detail="Internal server error during email validation",
                            )

                    if (
                        request_data.wallet is not None
                        and "balance" in request_data.wallet
                    ):
                        try:
                            new_balance = float(request_data.wallet["balance"])
                            if new_balance != user.wallet.balance:
                                update_fields["wallet.balance"] = new_balance
                                changes["wallet.balance"] = {
                                    "old": user.wallet.balance,
                                    "new": new_balance,
                                }
                        except (TypeError, ValueError):
                            raise HTTPException(
                                status_code=400, detail="Invalid balance value"
                            )

                    if request_data.currentSubscription is not None:
                        sub_data = request_data.currentSubscription
                        new_subscription = {}

                        if "planId" in sub_data:
                            if sub_data["planId"] is None or sub_data["planId"] == "":
                                new_subscription["planId"] = None
                                new_subscription["endDate"] = None
                            else:
                                try:
                                    plan_id = PydanticObjectId(sub_data["planId"])
                                    plan = await SubscriptionPlan.get(
                                        plan_id, session=session
                                    )
                                    if not plan:
                                        raise HTTPException(
                                            status_code=404,
                                            detail="Subscription plan not found",
                                        )

                                    new_subscription["planId"] = plan_id

                                    if plan.price == 0:
                                        new_subscription["endDate"] = None

                                except (
                                    ValidationError,
                                    beanie_exceptions.DocumentNotFound,
                                    ValueError,
                                ) as e:
                                    logger.error(
                                        f"Invalid planId format or plan not \
                                        found: {sub_data['planId']} - {e}",
                                        exc_info=True,
                                    )
                                    raise HTTPException(
                                        status_code=400,
                                        detail="Invalid planId format or plan not found",
                                    )

                        simple_fields = [
                            "isActive",
                            "autoRenew",
                            "adminNote",
                            "startDate",
                            "endDate",
                        ]
                        for field in simple_fields:
                            if field in sub_data:
                                new_subscription[field] = sub_data[field]

                        if new_subscription:
                            current_sub = (
                                user.currentSubscription.model_dump(by_alias=True)
                                if user.currentSubscription
                                else {}
                            )
                            merged_sub = {**current_sub, **new_subscription}

                            if (
                                "planId" in merged_sub
                                and merged_sub["planId"] is not None
                            ):
                                merged_sub["planId"] = PydanticObjectId(
                                    merged_sub["planId"]
                                )

                            update_fields["currentSubscription"] = merged_sub
                            changes["currentSubscription"] = {
                                "old": current_sub,
                                "new": merged_sub,
                            }

                    if update_fields:
                        await User.find_one({"_id": userId}).update(
                            {"$set": update_fields}, session=session
                        )
                        updated_user = await User.get(userId, session=session)

                        await log_admin_action(
                            admin_user,
                            request,
                            "update",
                            "User",
                            userId,
                            changes,
                            f"Admin {admin_user.email} updated user {userId}",
                        )

                    await session.commit_transaction()

                    user_data = updated_user.model_dump(by_alias=True)
                    user_data["_id"] = str(user_data["_id"])

                    if user_data.get("currentSubscription"):
                        if user_data["currentSubscription"].get("planId"):
                            user_data["currentSubscription"]["planId"] = str(
                                user_data["currentSubscription"]["planId"]
                            )
                        else:
                            user_data["currentSubscription"]["planId"] = None

                    return {"success": True, "user": user_data}

                except HTTPException as http_exc:
                    await session.abort_transaction()
                    raise http_exc
                except Exception as e:
                    await session.abort_transaction()
                    logger.error(f"Error updating user: {str(e)}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    async def admin_delete_user(
        userId: PydanticObjectId, request: Request, admin_user: User
    ):
        """
        **Метод для удаления пользователя администратором.**
        Принимает ID пользователя и удаляет его из базы данных.
        **Параметры:**
        - `userId`: ID пользователя, которого нужно удалить.
        **Возвращает:**
        - `success`: Успех операции.
        - `message`: Сообщение об успешном удалении.
        """
        try:
            client = get_motor_client()
        except RuntimeError as e:
            logger.error(
                f"MongoDB client not initialized for admin_delete_user: {e}",
                exc_info=False,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        async with await client.start_session() as session:
            async with session.start_transaction():
                try:
                    user = await User.get(userId, session=session)
                    if not user:
                        raise HTTPException(status_code=404, detail="User not found")

                    await log_admin_action(
                        admin_user,
                        request,
                        "delete",
                        "User",
                        userId,
                        {"user": user.model_dump(by_alias=True)},
                        f"Admin {admin_user.email} deleted user {userId}",
                    )

                    await User.find_one({"_id": userId}).delete(session=session)

                    await session.commit_transaction()

                    return {"success": True, "message": "User deleted successfully"}

                except HTTPException as http_exc:
                    await session.abort_transaction()
                    raise http_exc
                except Exception as e:
                    await session.abort_transaction()
                    logger.error(f"Error deleting user: {str(e)}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Internal server error")
