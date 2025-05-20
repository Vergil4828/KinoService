# backend/core/dependencies.py
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from jose import JWTError, jwt
import bcrypt # Для хеширования паролей, если он тут используется
from fastapi import HTTPException, Depends, status, Request
from beanie.odm.fields import PydanticObjectId

# Импортируем logger и секретные ключи из config.py
from backend.core.config import (
    logger,
    JWT_SECRET_KEY,
    REFRESH_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES, # Может понадобиться, если generate_tokens здесь
    REFRESH_TOKEN_EXPIRE_DAYS # Может понадобиться
)

# Импортируем необходимые модели
from backend.models.user import User
from backend.models.admin_action import AdminAction

# Функция для генерации токенов
def generate_tokens(user: User) -> Dict[str, str]:
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_payload = {
        "userId": str(user.id),
        "role": user.role,
        "exp": datetime.now(timezone.utc) + access_token_expires
    }

    refresh_payload = {
        "userId": str(user.id),
        "role": user.role,
        "exp": datetime.now(timezone.utc) + refresh_token_expires
    }

    access_token = jwt.encode(access_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return {
        "accessToken": access_token,
        "refreshToken": refresh_token
    }

# Dependency для получения текущего пользователя
async def get_current_user(request: Request) -> User:
    """FastAPI Dependency to get the current authenticated user."""
    auth_header = request.headers.get('Authorization')
    x_access_token = request.headers.get('x-access-token')
    token = None
    if auth_header:
        try:
            scheme, param = auth_header.split()
            if scheme.lower() == 'bearer':
                token = param
        except ValueError: pass
    elif x_access_token:
        token = x_access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Нет токена",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("userId")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный токен (нет userId)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await User.get(PydanticObjectId(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный токен доступа",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Ошибка в get_current_user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при аутентификации",
        )

# Dependency для проверки админ-прав
async def get_admin_user(current_user: User = Depends(get_current_user)):
    """FastAPI Dependency to check if the authenticated user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для администраторов",
        )
    return current_user

# Функция для логирования действий администратора
async def log_admin_action(
    admin_user: User,
    request: Request,
    action_type: str,
    target_model: str,
    target_id: Optional[PydanticObjectId] = None,
    changes: Optional[Dict[str, Any]] = None,
    additional_info: Optional[str] = None
):
    now_utc = datetime.now(timezone.utc)
    """Logs an administrative action."""
    try:
        admin_action = AdminAction(
            adminId=admin_user.id,
            actionType=action_type,
            targetModel=target_model,
            targetId=target_id,
            changes=changes,
            ipAddress=request.client.host if request.client else None,
            userAgent=request.headers.get('user-agent'),
            additionalInfo=additional_info,
            createdAt=now_utc,
            updatedAt=now_utc
        )
        await admin_action.insert()
    except Exception as err:
        logger.error(f'Ошибка при записи действия администратора: {err}', exc_info=True)