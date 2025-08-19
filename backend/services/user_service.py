import logging
import os
import shutil
import uuid
import aiofiles
import aiofiles.os
import re
from datetime import datetime, timezone
import bcrypt
from backend.core.config import (
    logger,
    PUBLIC_DIR,
    AVATAR_UPLOAD_DIR,
    REFRESH_SECRET_KEY,
    JWT_ALGORITHM,
)
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status, Request, UploadFile, File, Depends
from typing import Dict, Any
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from pathlib import Path
from beanie.odm.fields import PydanticObjectId
from backend.core.config import logger
from backend.core.dependencies import generate_tokens, get_current_user
from backend.core.redis_client import get_redis_client
from backend.models.user import User
from backend.models.subscription import SubscriptionPlan, SubscriptionHistory
from backend.models.transaction import Transaction
from backend.models.embedded import CurrentSubscriptionEmbedded
from backend.models.embedded import NotificationsEmbedded
from backend.models.embedded import WalletEmbedded
from backend.schemas.token import RefreshTokenRequest
from backend.schemas.user import (
    CreateUserRequest,
    LoginUserRequest,
    UserResponseBase,
    UpdateUserRequest,
)


class UserService:
    @staticmethod
    async def create_user(request_data: CreateUserRequest) -> Dict[str, Any]:
        """
        **Метод для создания нового пользователя.**
        Принимает данные о пользователе и создает нового пользователя в базе данных.
        **Параметры:**
        - `request_data`: Данные о пользователе (имя, email, пароль и т.д.).
        **Возвращает:**
        - `user`: Объект созданного пользователя с его данными.
        """
        try:
            basic_plan = await SubscriptionPlan.find_one({"price": 0})
            if not basic_plan:
                logger.error("Базовый тарифный план не найден при регистрации")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка сервера: Базовый тарифный план не найден",
                )

            hashed_password_bytes = bcrypt.hashpw(
                request_data.password.encode("utf-8"), bcrypt.gensalt()
            )
            hashed_password_str = hashed_password_bytes.decode("utf-8")

            now = datetime.now(timezone.utc)

            plan_data = {
                "id": str(basic_plan.id),
                "name": basic_plan.name,
                "price": basic_plan.price,
                "features": basic_plan.features,
                "renewalPeriod": basic_plan.renewalPeriod,
                "createdAt": basic_plan.createdAt,
                "updatedAt": basic_plan.updatedAt,
            }

            user = User(
                username=request_data.username,
                email=request_data.email,
                password=hashed_password_str,
                notifications=request_data.notifications or NotificationsEmbedded(),
                currentSubscription=CurrentSubscriptionEmbedded(
                    planId=basic_plan.id,
                    startDate=now,
                    endDate=None,
                    isActive=True,
                    autoRenew=False,
                    plan=plan_data,
                ),
                wallet=WalletEmbedded(balance=0.0, transactionIds=[]),
                role="user",
                createdAt=now,
                updatedAt=now,
            )

            await user.insert()
            tokens = await generate_tokens(user)

            response_data = {
                "message": "Пользователь создан",
                "success": True,
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "avatar": user.avatar,
                    "createdAt": user.createdAt.isoformat(),
                    "role": user.role,
                    "subscription": {
                        "currentPlan": {
                            "planId": str(user.currentSubscription.planId),
                            "startDate": user.currentSubscription.startDate.isoformat(),
                            "endDate": None,
                            "isActive": True,
                            "autoRenew": False,
                            "plan": plan_data,
                        },
                        "history": [],
                    },
                    "wallet": {"balance": 0, "transactions": []},
                },
                "accessToken": tokens["accessToken"],
                "refreshToken": tokens["refreshToken"],
            }

            return response_data

        except DuplicateKeyError as e:
            logger.warning(
                f"Попытка создания пользователя с существующим email: {request_data.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email уже занят"
            )
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка сервера при создании пользователя",
            )

    @staticmethod
    async def login_user(request_data: LoginUserRequest) -> Dict[str, Any]:
        """
        **Метод для входа пользователя в систему.**
        Принимает email и пароль пользователя.
        **Возвращает:**
        - `access_token`: JWT токен для аутентификации в последующих запросах.
        - `refresh_token`: Токен для обновления `access_token`.
        """
        try:
            user = await User.find_one(User.email == request_data.email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            if not bcrypt.checkpw(
                request_data.password.encode("utf-8"), user.password.encode("utf-8")
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            tokens = await generate_tokens(user)

            user_data = user.model_dump(by_alias=True)
            user_data["_id"] = str(user_data["_id"])
            user_response = UserResponseBase(**user_data).model_dump(by_alias=True)

            return {
                "success": True,
                "accessToken": tokens["accessToken"],
                "refreshToken": tokens["refreshToken"],
                "user": user_response,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during login",
            )

    @staticmethod
    async def get_user_data(current_user: User) -> Dict[str, Any]:
        """
        **Метод для получения данных пользователя.**
        Принимает объект пользователя и возвращает его данные.
        **Параметры:**
        - `current_user`: Объект текущего пользователя.
        **Возвращает:**
        - `user`: Объект пользователя с его данными.
        """
        try:
            user = await User.get(current_user.id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            current_subscription = None
            if user.currentSubscription and user.currentSubscription.planId:
                plan = await SubscriptionPlan.get(user.currentSubscription.planId)
                current_subscription = {
                    "planId": str(user.currentSubscription.planId),
                    "startDate": (
                        user.currentSubscription.startDate.isoformat()
                        if user.currentSubscription.startDate
                        else None
                    ),
                    "endDate": (
                        user.currentSubscription.endDate.isoformat()
                        if user.currentSubscription.endDate
                        else None
                    ),
                    "isActive": user.currentSubscription.isActive,
                    "autoRenew": user.currentSubscription.autoRenew,
                    "plan": (
                        {
                            "id": str(plan.id),
                            "name": plan.name,
                            "price": plan.price,
                            "features": plan.features,
                        }
                        if plan
                        else None
                    ),
                }

            transactions = []
            if user.wallet.transactionIds:
                transactions = (
                    await Transaction.find({"_id": {"$in": user.wallet.transactionIds}})
                    .sort(-Transaction.date)
                    .limit(50)
                    .to_list()
                )
                transactions = [
                    {
                        "id": str(tx.id),
                        "amount": tx.amount,
                        "type": tx.type,
                        "date": tx.date.isoformat(),
                        "description": tx.description,
                    }
                    for tx in transactions
                ]

            subscription_history = (
                await SubscriptionHistory.find(SubscriptionHistory.userId == user.id)
                .sort(-SubscriptionHistory.startDate)
                .to_list()
            )
            subscription_history = [
                {
                    "id": str(sh.id),
                    "planId": str(sh.planId),
                    "startDate": sh.startDate.isoformat(),
                    "endDate": sh.endDate.isoformat(),
                    "isActive": sh.isActive,
                    "autoRenew": sh.autoRenew,
                }
                for sh in subscription_history
            ]

            return {
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "avatar": user.avatar,
                    "createdAt": user.createdAt.isoformat() if user.createdAt else None,
                    "wallet": {
                        "balance": user.wallet.balance,
                        "transactions": transactions,
                    },
                    "subscription": {
                        "currentPlan": current_subscription,
                        "history": subscription_history,
                    },
                }
            }

        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    async def update_user(
        request_data: UpdateUserRequest, current_user: User
    ) -> Dict[str, Any]:
        """
        **Метод для обновления данных пользователя.**
        Принимает объект пользователя и данные для обновления.
        **Параметры:**
        - `request_data`: Данные для обновления (имя, email, пароль и т.д.).
        - `current_user`: Объект текущего пользователя.
        **Возвращает:**
        - `user`: Объект обновленного пользователя с его данными.
        """
        is_match = bcrypt.checkpw(
            request_data.currentPassword.encode("utf-8"),
            current_user.password.encode("utf-8"),
        )
        if not is_match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный текущий пароль",
            )

        if request_data.email is not None and request_data.email != current_user.email:
            existing_user = await User.find_one(
                {"email": request_data.email, "_id": {"$ne": current_user.id}}
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email уже используется",
                )

        if request_data.username is not None:
            current_user.username = request_data.username
        if request_data.email is not None:
            current_user.email = request_data.email
        if request_data.newPassword is not None:
            hashed_new_password_bytes = bcrypt.hashpw(
                request_data.newPassword.encode("utf-8"), bcrypt.gensalt()
            )
            current_user.password = hashed_new_password_bytes.decode("utf-8")

        try:
            await current_user.save()

            user_data_dict = current_user.model_dump(by_alias=True)
            user_data_dict["_id"] = str(user_data_dict["_id"])
            user_response_instance = UserResponseBase(**user_data_dict)
            final_user_response_dict = user_response_instance.model_dump(by_alias=True)

            return {
                "success": True,
                "message": "Профиль успешно обновлен",
                "user": final_user_response_dict,
            }

        except DuplicateKeyError as e:
            logger.warning(
                f"Попытка обновления пользователя с существующим email: {request_data.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже используется"
            )
        except Exception as e:
            logger.error(f"Ошибка при обновлении пользователя: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка сервера при обновлении профиля",
            )

    @staticmethod
    async def logout_user(
        request: Request, current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """
        **Метод для выхода пользователя из системы.**
        **Возвращает:**
        - `success`: True, если выход успешен.
        - `message`: Сообщение об успешном выходе.
        """
        try:
            redis_client = get_redis_client()
            await redis_client.delete(f"refresh_token:{current_user.id}")
            logger.info(f"Refresh token for user {current_user.id} has been revoked.")

            return {"success": True, "message": "Logout successful"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Logout confirmation error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during logout confirmation",
            )

    @staticmethod
    async def refresh_access_token(request_data: RefreshTokenRequest) -> Dict[str, Any]:
        """
        **Метод для обновления access-токена.**
        Принимает refresh-токен и возвращает новый access-токен.
        **Параметры:**
        - `request_data`: Данные с refresh-токеном.
        **Возвращает:**
        - `access_token`: Новый JWT токен для аутентификации в последующих запросах.
        - `refresh_token`: Новый токен для обновления `access_token`.
        """
        try:
            refresh_token = request_data.refreshToken

            try:
                payload = jwt.decode(
                    refresh_token, REFRESH_SECRET_KEY, algorithms=[JWT_ALGORITHM]
                )
                user_id = payload.get("userId")
                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token format",
                    )

            except ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                )
            except JWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            redis_client = get_redis_client()
            stored_token = await redis_client.get(f"refresh_token:{user_id}")
            if not stored_token or stored_token.decode("utf-8") != refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )

            user = await User.get(PydanticObjectId(user_id))
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
                )

            tokens = await generate_tokens(user)

            return {
                "success": True,
                "accessToken": tokens["accessToken"],
                "refreshToken": tokens["refreshToken"],
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Refresh token error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @staticmethod
    async def upload_avatar(
        avatar: UploadFile = File(...), current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """
        **Метод для загрузки аватара пользователя.**
        Принимает файл аватара и текущего пользователя.
        **Параметры:**
        - `avatar`: Файл аватара.
        - `current_user`: Объект текущего пользователя.
        **Возвращает:**
        - `success`: True, если загрузка успешна.
        - `avatarUrl`: URL загруженного аватара.
        - `user`: Объект обновленного пользователя с его данными.
        """
        if not avatar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Файл не загружен"
            )

        def get_real_file_type(file_content):
            if file_content.startswith(b"\xff\xd8\xff"):
                return "image/jpeg"
            elif file_content.startswith(b"\x89PNG\r\n\x1a\n"):
                return "image/png"
            elif file_content.startswith(b"GIF87a") or file_content.startswith(
                b"GIF89a"
            ):
                return "image/gif"
            return "invalid"

        content = await avatar.read()
        await avatar.seek(0)

        file_size = len(content)
        if file_size > 2 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Размер файла превышает 2MB.",
            )

        real_file_type = get_real_file_type(content)
        allowed_types = ["image/jpeg", "image/png", "image/gif"]

        if real_file_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Разрешены только файлы изображений (JPEG, PNG, GIF).",
            )
        allowed_image_types = ["image/jpeg", "image/png", "image/gif"]
        if avatar.content_type not in allowed_image_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Разрешены только файлы изображений (JPEG, PNG, GIF).",
            )

        try:

            unique_suffix = uuid.uuid4().hex
            user_upload_dir = AVATAR_UPLOAD_DIR / str(current_user.id)
            os.makedirs(user_upload_dir, exist_ok=True)

            file_extension = Path(avatar.filename).suffix
            new_filename = f"{current_user.id}-{unique_suffix}{file_extension}"
            file_path = user_upload_dir / new_filename

            async with aiofiles.open(file_path, "wb") as out_file:
                await out_file.write(content)

            avatar_url = f"/public/uploads/avatars/{current_user.id}/{new_filename}"

            if current_user.avatar and current_user.avatar.startswith(
                "/public/uploads/avatars/"
            ):
                old_avatar_relative_path = current_user.avatar.replace(
                    "/public/", "", 1
                )
                old_avatar_full_path = PUBLIC_DIR / old_avatar_relative_path

                if old_avatar_full_path.exists() and old_avatar_full_path != file_path:
                    try:
                        await aiofiles.os.remove(old_avatar_full_path)
                        logger.info(f"Удален старый аватар: {old_avatar_full_path}")
                    except FileNotFoundError:
                        logger.warning(
                            f"Старый аватар не найден для удаления: {old_avatar_full_path}"
                        )
                    except Exception as delete_err:
                        logger.error(
                            f"Ошибка при удалении старого аватара {old_avatar_full_path}: {delete_err}",
                            exc_info=True,
                        )

            current_user.avatar = avatar_url
            await current_user.save()

            user_data_dict = current_user.model_dump(by_alias=True)
            user_data_dict["_id"] = str(user_data_dict["_id"])
            user_response_instance = UserResponseBase(**user_data_dict)
            final_user_response_dict = user_response_instance.model_dump(by_alias=True)

            return {
                "success": True,
                "avatarUrl": avatar_url,
                "user": final_user_response_dict,
            }

        except Exception as e:
            logger.error(f"Ошибка при загрузке аватара: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка сервера при загрузке аватара",
            )
