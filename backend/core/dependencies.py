from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from jose import JWTError, jwt, ExpiredSignatureError
from fastapi import HTTPException, Depends, status, Request
from beanie.odm.fields import PydanticObjectId
from backend.core.redis_client import get_redis_client

from backend.core.config import (
    logger,
    JWT_SECRET_KEY,
    REFRESH_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


from backend.models.user import User
from backend.models.admin import AdminAction


async def save_refresh_token_in_redis(
    user_id: str, refresh_token: str, expires: timedelta
):
    redis_client = get_redis_client()
    await redis_client.set(f"refresh_token:{user_id}", refresh_token, ex=expires)


async def generate_tokens(user: User) -> Dict[str, str]:
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_payload = {
        "userId": str(user.id),
        "role": user.role,
        "exp": datetime.now(timezone.utc) + access_token_expires,
    }

    refresh_payload = {
        "userId": str(user.id),
        "role": user.role,
        "exp": datetime.now(timezone.utc) + refresh_token_expires,
    }

    access_token = jwt.encode(access_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(
        refresh_payload, REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM
    )

    await save_refresh_token_in_redis(
        str(user.id), refresh_token, refresh_token_expires
    )
    return {"accessToken": access_token, "refreshToken": refresh_token}


async def get_current_user(request: Request) -> User:
    try:

        auth_header = request.headers.get("Authorization")
        x_access_token = request.headers.get("x-access-token")
        token = None

        if auth_header:
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    raise ValueError("Invalid scheme")
            except ValueError:
                token = None

        if not token and x_access_token:
            token = x_access_token

        if not token:
            logger.warning("Недостаточно прав доступа")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("userId")

            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format",
                )

            user = await User.get(PydanticObjectId(user_id))
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )

            return user

        except ExpiredSignatureError:
            logger.warning("Access token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            logger.warning(f"JWT validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected auth error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )


async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для администраторов",
        )
    return current_user


async def log_admin_action(
    admin_user: User,
    request: Request,
    action_type: str,
    target_model: str,
    target_id: Optional[PydanticObjectId] = None,
    changes: Optional[Dict[str, Any]] = None,
    additional_info: Optional[str] = None,
):
    now_utc = datetime.now(timezone.utc)
    try:
        admin_action = AdminAction(
            adminId=admin_user.id,
            actionType=action_type,
            targetModel=target_model,
            targetId=target_id,
            changes=changes,
            ipAddress=request.client.host if request.client else None,
            userAgent=request.headers.get("user-agent"),
            additionalInfo=additional_info,
            createdAt=now_utc,
            updatedAt=now_utc,
        )
        await admin_action.insert()
    except Exception as err:
        logger.error(f"Ошибка при записи действия администратора: {err}", exc_info=True)
