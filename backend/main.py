import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status, Request, UploadFile, File, Form, Query
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import json
from motor.motor_asyncio import AsyncIOMotorClient
from beanie.odm.fields import PydanticObjectId

from motor.core import AgnosticClientSession as AsyncIOMotorSession
from beanie import init_beanie, Document, Indexed, PydanticObjectId, Link
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Union
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from pydantic import Field, BaseModel, ConfigDict, field_validator, EmailStr, validator
from pydantic_core.core_schema import ValidationInfo
from pathlib import Path
from jose import JWTError, jwt
import bcrypt 
import pytz 

from pymongo import IndexModel, MongoClient
from pymongo.errors import DuplicateKeyError, ConfigurationError, OperationFailure, InvalidOperation, ServerSelectionTimeoutError 
import shutil 
import uuid 
import aiofiles 
import aiofiles.os 
import re
import math 


from models import (
    User,
    SubscriptionPlan,
    SubscriptionHistory,
    UserStats,
    Transaction,
    AdminAction,
    RefreshTokenEmbedded,
    CurrentSubscriptionEmbedded,
    SubscriptionHistoryEmbedded,
    WalletEmbedded,
    NotificationsEmbedded,
    SubscriptionPlanResponse,
    SubscriptionHistoryResponse,
    TransactionResponse,
    UserResponseBase,
    PurchaseSubscriptionResponse,
    AdminActionResponse,
    CreateUserRequest,
    LoginUserRequest,
    UpdateUserRequest,
    RefreshTokenRequest,
    DepositWalletRequest,
    WithdrawWalletRequest,
    PurchaseSubscriptionRequest,
    AdminChangePlanRequest,
    AdminChangeUserRequest
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


script_dir = Path(__file__).parent
project_root = script_dir.parent
dotenv_path = project_root / ".env"

load_dotenv(dotenv_path=dotenv_path)


app = FastAPI()

PORT = os.getenv("PORT") 
SECRET_KEY = os.getenv("JWT_SECRET")
REFRESH_KEY = os.getenv("REFRESH_SECRET")
MONGO_URI = os.getenv("MONGO_URI")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


if not SECRET_KEY:
    logger.error("Переменная окружения JWT_SECRET не установлена!")
    exit(1)
if not REFRESH_KEY:
    logger.error("Переменная окружения REFRESH_SECRET не установлена!")
    exit(1)
if not MONGO_URI and not os.getenv("MONGO_DB_NAME"):
    logger.error("Переменные окружения MONGO_URI или MONGO_DB_NAME не установлены!")
    exit(1)


allowed_origins = [
    'https://vosmerka228.ru',
    'https://api.vosmerka228.ru',
    'http://localhost:5173',
    'https://m.vosmerka228.ru'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "x-access-token"],
)


# Рекурсивные ссылки в Pydantic моделях
SubscriptionPlanResponse.model_rebuild()
SubscriptionHistoryEmbedded.model_rebuild()
CurrentSubscriptionEmbedded.model_rebuild()
WalletEmbedded.model_rebuild()
NotificationsEmbedded.model_rebuild()
RefreshTokenEmbedded.model_rebuild()
TransactionResponse.model_rebuild()
AdminActionResponse.model_rebuild()
UserResponseBase.model_rebuild()



motor_client: Optional[AsyncIOMotorClient] = None

async def init_db():
    logger.info("Попытка подключения к MongoDB...")
    try:
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        dotenv_path = project_root / ".env"
        logger.info(f"Ожидаемый путь к .env: {dotenv_path}")

        load_dotenv(dotenv_path=dotenv_path)

        loaded_mongo_uri = os.getenv("MONGO_URI")
        logger.info(f"Загруженное значение MONGO_URI: {loaded_mongo_uri}")

        loaded_mongo_db_name = os.getenv("MONGO_DB_NAME")
        logger.info(f"Загруженное значение MONGO_DB_NAME: {loaded_mongo_db_name}")


        global motor_client
        motor_client = AsyncIOMotorClient(loaded_mongo_uri, serverSelectionTimeoutMS=5000)


        await motor_client.admin.command('ping')
        logger.info("Подключение к MongoDB успешно установлено")

        db_name = loaded_mongo_db_name

        if not db_name:
            try:
                db_name = motor_client.get_default_database().name
                logger.info("Получено имя базы данных из MONGO_URI")
            except ConfigurationError:
                logger.error("MONGO_URI не содержит имя базы данных, и переменная окружения MONGO_DB_NAME не установлена.")
                raise ConfigurationError("No default database name defined or provided in MONGO_URI or MONGO_DB_NAME environment variable.")
        else:
             logger.info(f"Получено имя базы данных из MONGO_DB_NAME: {db_name}")


        logger.info(f"Подключение к базе данных: {db_name}")


        await init_beanie(database=motor_client[db_name], document_models=[
            User,
            SubscriptionPlan,
            SubscriptionHistory,
            UserStats,
            Transaction,
            AdminAction,
        ])
        logger.info("Успешное подключение к MongoDB и инициализация Beanie")

        await initSubscriptionPlans()

        scheduler = AsyncIOScheduler()
        scheduler.add_job(checkAndUpdateSubscriptions, 'interval', minutes=1)
        scheduler.start()
        logger.info('Cron-задача для проверки подписок активирована')

    except ServerSelectionTimeoutError as sste:
        logger.error(f"Ошибка подключения к MongoDB: Таймаут подключения к серверу. Проверьте, запущен ли MongoDB и доступен ли он по адресу {loaded_mongo_uri}.", exc_info=True)
        exit(1)
    except ConfigurationError as ce:
         logger.error(f"Ошибка конфигурации базы данных: {ce}", exc_info=True)
         exit(1)
    except Exception as e:
        logger.error(f"Неожиданная ошибка подключения к MongoDB или инициализации: {e}", exc_info=True)
        exit(1)


async def initSubscriptionPlans():
    logger.info("Проверка и инициализация тарифных планов...")
    try:
        plans_count = await SubscriptionPlan.count()

        if plans_count > 0:
            logger.info('Тарифные планы уже существуют, инициализация не требуется')
            return

        plans_data = [
            {"name": "Базовый", "price": 0, "renewalPeriod": 30, "features": ["Full HD качество", "1 устройство", "С рекламой"]},
            {"name": "Популярный", "price": 899, "renewalPeriod": 30, "features": ["4K Ultra HD + HDR", "До 5 устройств", "Без рекламы", "Оффлайн просмотр"]},
            {"name": "Премиум+", "price": 1199, "renewalPeriod": 30, "features": ["4K Ultra HD + HDR + Dolby Vision", "До 7 устройств", "Без рекламы + ранний доступ", "Оффлайн-просмотр + эксклюзивы"]}
        ]

        plan_documents = [SubscriptionPlan(**plan) for plan in plans_data]
        await SubscriptionPlan.insert_many(plan_documents)
        logger.info(f'Тарифные планы успешно инициализированы: {len(plan_documents)} добавлено')

    except Exception as e:
        logger.error(f'Ошибка при инициализации тарифных планов: {e}', exc_info=True)



async def checkAndUpdateSubscriptions():
    """
    Checks for expired subscriptions and moves users to the basic plan.
    Uses MongoDB transactions.
    """
    if motor_client is None:
         logger.error("Ошибка при проверки подписок: Клиент MongoDB не инициализирован. Задача пропущена.")
         return

    client = motor_client

    async with await client.start_session() as session:
        async with session.start_transaction():
            try:
                now_utc = datetime.now(timezone.utc)
                logger.info(f"[{now_utc.isoformat()}] Запуск проверки подписок...")

                users_to_update = await User.find({
                    'currentSubscription.endDate': {
                        '$lte': now_utc,
                        '$ne': None
                    },
                    'currentSubscription.isActive': True
                }, session=session).to_list()

                logger.info(f"Найдено {len(users_to_update)} пользователей для обновления")

                basic_plan = await SubscriptionPlan.find_one(SubscriptionPlan.price == 0, session=session)
                if not basic_plan:
                    raise Exception('Базовый тарифный план не найден')

                for user in users_to_update:
                    if user.currentSubscription and user.currentSubscription.planId:
                         history_entry = SubscriptionHistory(
                              userId=user.id,
                              planId=user.currentSubscription.planId,
                              startDate=user.currentSubscription.startDate or datetime.now(timezone.utc),
                              endDate=now_utc,
                              isActive=False,
                              autoRenew=user.currentSubscription.autoRenew
                         )
                         await history_entry.insert(session=session)
                         logger.info(f"История подписки пользователя {user.id} добавлена в отдельную коллекцию")

                    user.currentSubscription = CurrentSubscriptionEmbedded(
                         planId=basic_plan.id,
                         startDate=datetime.now(timezone.utc),
                         endDate=None,
                         isActive=True,
                         autoRenew=False
                    )

                    await user.save(session=session)
                    logger.info(f"Пользователь {user.id} переведен на базовый тариф")

                await session.commit_transaction()
                logger.info('Проверка подписок завершена успешно')

            except Exception as error:
                await session.abort_transaction()
                logger.error(f'Ошибка при проверке подписок: {error}', exc_info=True)


def generate_tokens(user: User):
    access_token_expires = timedelta(minutes=15)
    refresh_token_expires = timedelta(days=7)
    
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

    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, REFRESH_KEY, algorithm=JWT_ALGORITHM)

    return {
        "accessToken": access_token, 
        "refreshToken": refresh_token
    }


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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
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

async def get_admin_user(current_user: User = Depends(get_current_user)):
    """FastAPI Dependency to check if the authenticated user is an admin."""
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

static_files_dir = project_root / "public"
if not os.path.isdir(static_files_dir):
     logger.warning(f"Директория статических файлов не найдена: {static_files_dir}. Статические файлы могут быть недоступны.")

app.mount("/public", StaticFiles(directory=static_files_dir), name="static")

AVATAR_UPLOAD_DIR = static_files_dir / "uploads" / "avatars"
os.makedirs(AVATAR_UPLOAD_DIR, exist_ok=True)


@app.post('/api/create/user', status_code=status.HTTP_201_CREATED)
async def create_user(request_data: CreateUserRequest):
    try:
        basic_plan = await SubscriptionPlan.find_one(SubscriptionPlan.price == 0)
        if not basic_plan:
            logger.error("Базовый тарифный план не найден при регистрации")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail='Ошибка сервера: Базовый тарифный план не найден'
            )

        hashed_password_bytes = bcrypt.hashpw(request_data.password.encode('utf-8'), bcrypt.gensalt())
        hashed_password_str = hashed_password_bytes.decode('utf-8')

        now = datetime.now(timezone.utc)
        
        plan_data = {
            "id": str(basic_plan.id),
            "name": basic_plan.name,
            "price": basic_plan.price,
            "features": basic_plan.features,
            "renewalPeriod": basic_plan.renewalPeriod,
            "createdAt": basic_plan.createdAt,
            "updatedAt": basic_plan.updatedAt
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
                plan=plan_data 
            ),
            wallet=WalletEmbedded(balance=0.0, transactionIds=[]),
            role="user",
            createdAt=now,
            updatedAt=now
        )

        await user.insert()
        tokens = generate_tokens(user)

        response_data = {
            'message': 'Пользователь создан',
            'success': True,
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'avatar': user.avatar,
                'createdAt': user.createdAt.isoformat(),
                'role': user.role,
                'subscription': {
                    'currentPlan': {
                        'planId': str(user.currentSubscription.planId),
                        'startDate': user.currentSubscription.startDate.isoformat(),
                        'endDate': None,
                        'isActive': True,
                        'autoRenew': False,
                        'plan': plan_data 
                    },
                    'history': []
                },
                'wallet': {
                    'balance': 0,
                    'transactions': []
                }
            },
            'accessToken': tokens['accessToken'],
            'refreshToken': tokens['refreshToken']
        }

        return response_data

    except DuplicateKeyError as e:
        logger.warning(f"Попытка создания пользователя с существующим email: {request_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail='Email уже занят'
        )
    except Exception as e:
        logger.error(f'Ошибка при создании пользователя: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Ошибка сервера при создании пользователя'
        )
        
@app.post('/api/login/user')
async def login_user(request_data: LoginUserRequest):
    try:
        user = await User.find_one(User.email == request_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or password"
            )

        if not bcrypt.checkpw(request_data.password.encode('utf-8'), user.password.encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or password"
            )

        tokens = generate_tokens(user)
        
        user_data = user.model_dump(by_alias=True)
        user_data['_id'] = str(user_data['_id'])
        user_response = UserResponseBase(**user_data).model_dump(by_alias=True)

        return {
            'success': True,
            'accessToken': tokens['accessToken'],
            'refreshToken': tokens['refreshToken'],
            'user': user_response
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Login error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@app.get('/api/user/data')
async def get_user_data(current_user: User = Depends(get_current_user)):
    try:
        user = await User.get(current_user.id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        current_subscription = None
        if user.currentSubscription and user.currentSubscription.planId:
            plan = await SubscriptionPlan.get(user.currentSubscription.planId)
            current_subscription = {
                "planId": str(user.currentSubscription.planId),
                "startDate": user.currentSubscription.startDate.isoformat() if user.currentSubscription.startDate else None,
                "endDate": user.currentSubscription.endDate.isoformat() if user.currentSubscription.endDate else None,
                "isActive": user.currentSubscription.isActive,
                "autoRenew": user.currentSubscription.autoRenew,
                "plan": {
                    "id": str(plan.id),
                    "name": plan.name,
                    "price": plan.price,
                    "features": plan.features
                } if plan else None
            }

        transactions = []
        if user.wallet.transactionIds:
            transactions = await Transaction.find({"_id": {"$in": user.wallet.transactionIds}}).sort(-Transaction.date).limit(50).to_list()
            transactions = [{
                "id": str(tx.id),
                "amount": tx.amount,
                "type": tx.type,
                "date": tx.date.isoformat(),
                "description": tx.description
            } for tx in transactions]

        subscription_history = await SubscriptionHistory.find(SubscriptionHistory.userId == user.id).sort(-SubscriptionHistory.startDate).to_list()
        subscription_history = [{
            "id": str(sh.id),
            "planId": str(sh.planId),
            "startDate": sh.startDate.isoformat(),
            "endDate": sh.endDate.isoformat(),
            "isActive": sh.isActive,
            "autoRenew": sh.autoRenew
        } for sh in subscription_history]

        return {
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "avatar": user.avatar,
                "createdAt": user.createdAt.isoformat() if user.createdAt else None,
                "wallet": {
                    "balance": user.wallet.balance,
                    "transactions": transactions
                },
                "subscription": {
                    "currentPlan": current_subscription,
                    "history": subscription_history
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting user data: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put('/api/update/user')
async def update_user(request_data: UpdateUserRequest, current_user: User = Depends(get_current_user)):
    is_match = bcrypt.checkpw(request_data.currentPassword.encode('utf-8'), current_user.password.encode('utf-8'))
    if not is_match:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Неверный текущий пароль')

    if request_data.email is not None and request_data.email != current_user.email:
        existing_user = await User.find_one({"email": request_data.email, "_id": {"$ne": current_user.id}})
        if existing_user:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email уже используется')

    if request_data.username is not None:
        current_user.username = request_data.username
    if request_data.email is not None:
        current_user.email = request_data.email
    if request_data.newPassword is not None:
        hashed_new_password_bytes = bcrypt.hashpw(request_data.newPassword.encode('utf-8'), bcrypt.gensalt())
        current_user.password = hashed_new_password_bytes.decode('utf-8')


    try:
        await current_user.save()

        user_data_dict = current_user.model_dump(by_alias=True)
        user_data_dict['_id'] = str(user_data_dict['_id'])
        user_response_instance = UserResponseBase(**user_data_dict)
        final_user_response_dict = user_response_instance.model_dump(by_alias=True)

        return {
            'success': True,
            'message': 'Профиль успешно обновлен',
            'user': final_user_response_dict, 
        }

    except DuplicateKeyError as e:
         logger.warning(f"Попытка обновления пользователя с существующим email: {request_data.email}")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email уже используется')
    except Exception as e:
        logger.error(f'Ошибка при обновлении пользователя: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Ошибка сервера при обновлении профиля')


@app.post('/api/logout')
async def logout_user(request: Request):
    try:

        data = await request.json()
        refresh_token = data.get("refreshToken")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required"
            )

        result = await User.find_one(
            {"refreshTokens.token": refresh_token}
        ).update({
            "$pull": {"refreshTokens": {"token": refresh_token}}
        })

        if result.modified_count == 0:
            logger.warning(f"Refresh token not found during logout: {refresh_token}")

        return {
            "success": True,
            "message": "Logout successful"
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Logout error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

@app.post('/api/refresh-token')
async def refresh_access_token(request: Request):
    try:
        data = await request.json()
        refresh_token = data.get("refreshToken")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is required"
            )

        try:
            payload = jwt.decode(refresh_token, REFRESH_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("userId")
            
            if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token expired"
                )
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user = await User.get(PydanticObjectId(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        tokens = generate_tokens(user)
        
        return {
            'success': True,
            'accessToken': tokens['accessToken'],
            'refreshToken': tokens['refreshToken']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Refresh token error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post('/api/user/avatar')
async def upload_avatar(avatar: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if not avatar:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Файл не загружен')

    allowed_image_types = ['image/jpeg', 'image/png', 'image/gif']
    if avatar.content_type not in allowed_image_types:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Разрешены только файлы изображений (JPEG, PNG, GIF).')

    try:
        avatar.file.seek(0, os.SEEK_END)
        file_size = avatar.file.tell()
        await avatar.seek(0) 
        if file_size > 2 * 1024 * 1024: 
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Размер файла превышает 2MB.')


        unique_suffix = uuid.uuid4().hex
        user_upload_dir = AVATAR_UPLOAD_DIR / str(current_user.id)
        os.makedirs(user_upload_dir, exist_ok=True)

        file_extension = Path(avatar.filename).suffix
        new_filename = f"{current_user.id}-{unique_suffix}{file_extension}"
        file_path = user_upload_dir / new_filename

        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await avatar.read()
            await out_file.write(content)

        avatar_url = f"/public/uploads/avatars/{current_user.id}/{new_filename}"

        if current_user.avatar and current_user.avatar.startswith('/public/uploads/avatars/'):
             old_avatar_relative_path = current_user.avatar.replace("/public/", "", 1)
             old_avatar_full_path = project_root / "public" / old_avatar_relative_path

             if old_avatar_full_path.exists() and old_avatar_full_path != file_path:
                 try:
                     await aiofiles.os.remove(old_avatar_full_path)
                     logger.info(f"Удален старый аватар: {old_avatar_full_path}")
                 except FileNotFoundError:
                     logger.warning(f"Старый аватар не найден для удаления: {old_avatar_full_path}")
                 except Exception as delete_err:
                     logger.error(f'Ошибка при удалении старого аватара {old_avatar_full_path}: {delete_err}', exc_info=True)


        current_user.avatar = avatar_url
        await current_user.save()

        user_data_dict = current_user.model_dump(by_alias=True)
        user_data_dict['_id'] = str(user_data_dict['_id'])
        user_response_instance = UserResponseBase(**user_data_dict)
        final_user_response_dict = user_response_instance.model_dump(by_alias=True)

        return {
            'success': True,
            'avatarUrl': avatar_url,
            'user': final_user_response_dict 
        }

    except Exception as e:
        logger.error(f'Ошибка при загрузке аватара: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Ошибка сервера при загрузке аватара')



@app.get('/api/wallet')
async def get_wallet_data(current_user: User = Depends(get_current_user)):
    try:
        user = await User.get(current_user.id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        transactions = []
        if user.wallet.transactionIds:
            pipeline = [
                {"$match": {"_id": {"$in": user.wallet.transactionIds}}},
                {"$sort": {"date": -1}},
                {"$limit": 50},
                {"$project": {
                    "_id": {"$toString": "$_id"},
                    "userId": {"$toString": "$userId"},
                    "amount": 1,
                    "type": 1,
                    "status": 1,
                    "description": 1,
                    "paymentMethod": 1,
                    "currency": 1,
                    "date": {"$dateToString": {"format": "%Y-%m-%dT%H:%M:%S.%LZ", "date": "$date"}},
                    "createdAt": {"$dateToString": {"format": "%Y-%m-%dT%H:%M:%S.%LZ", "date": "$createdAt"}},
                    "updatedAt": {"$dateToString": {"format": "%Y-%m-%dT%H:%M:%S.%LZ", "date": "$updatedAt"}}
                }}
            ]
            
            transactions_cursor = Transaction.aggregate(pipeline)
            transactions = await transactions_cursor.to_list(length=50)

        return {
            "success": True,
            "balance": user.wallet.balance,
            "transactions": transactions
        }

    except Exception as e:
        logger.error(f"Error getting wallet data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post('/api/wallet/deposit')
async def deposit_wallet(request_data: DepositWalletRequest, current_user: User = Depends(get_current_user)):
    if motor_client is None:
         logger.error("Ошибка при пополнении кошелька: Клиент MongoDB не инициализирован.")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Ошибка сервера: База данных недоступна')

    client = motor_client
    async with await client.start_session() as session:
        async with session.start_transaction():
            try:
                now_utc = datetime.now(timezone.utc)

                transaction_data = Transaction(
                    userId=current_user.id,
                    amount=request_data.amount,
                    type='deposit',
                    status='completed',
                    paymentMethod=request_data.paymentMethod,
                    description=f"Пополнение баланса на {request_data.amount} RUB",
                    date=now_utc,
                    createdAt=now_utc,
                    updatedAt=now_utc
                )

                inserted_transactions_result = await Transaction.insert_many([transaction_data], session=session)
                inserted_transaction_id = inserted_transactions_result.inserted_ids[0]

                await User.find_one(User.id == current_user.id).update(
                    {"$inc": {'wallet.balance': request_data.amount},
                     "$push": {'wallet.transactionIds': inserted_transaction_id}},
                    session=session
                )

                updated_user = await User.get(current_user.id, session=session)

                await session.commit_transaction()

                transaction_data_dict = transaction_data.model_dump(by_alias=True)
                transaction_data_dict['_id'] = str(transaction_data_dict['_id'])
                transaction_response_instance = TransactionResponse(**transaction_data_dict)
                final_transaction_response_dict = transaction_response_instance.model_dump(by_alias=True)

                return {
                    'success': True,
                    'newBalance': updated_user.wallet.balance,
                    'transaction': final_transaction_response_dict
                }

            except Exception as err:
                await session.abort_transaction()
                logger.error(f'Ошибка при пополнении кошелька: {err}', exc_info=True)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

@app.post('/api/wallet/withdraw')
async def withdraw_wallet(request_data: WithdrawWalletRequest, current_user: User = Depends(get_current_user)):
    if motor_client is None:
         logger.error("Ошибка при списании средств: Клиент MongoDB не инициализирован.")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Ошибка сервера: База данных недоступна')

    client = motor_client
    async with await client.start_session() as session:
        async with session.start_transaction():
            try:
                now_utc = datetime.now(timezone.utc)

                user_in_session = await User.get(current_user.id, session=session)
                if user_in_session.wallet.balance < request_data.amount:
                    await session.abort_transaction()
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Недостаточно средств')

                await User.find_one(User.id == current_user.id).update(
                    {"$inc": {'wallet.balance': -request_data.amount},
                     "$set": {'wallet.lastTransaction': now_utc}},
                    session=session
                )

                transaction_data = Transaction(
                    userId=current_user.id,
                    amount=-request_data.amount,
                    type='withdrawal',
                    status='completed',
                    description=request_data.description or f"Списание {request_data.amount} RUB",
                    date=now_utc,
                    createdAt=now_utc,
                    updatedAt=now_utc
                )
                inserted_transactions = await Transaction.insert_many([transaction_data], session=session)
                inserted_transaction_id = inserted_transactions[0].id

                await User.find_one(User.id == current_user.id).update(
                   {"$push": {'wallet.transactionIds': inserted_transaction_id}},
                   session=session
                )

                updated_user = await User.get(current_user.id, session=session)

                await session.commit_transaction()

                transaction_data_dict = transaction_data.model_dump(by_alias=True)
                transaction_data_dict['_id'] = str(transaction_data_dict['_id'])
                transaction_response_instance = TransactionResponse(**transaction_data_dict)
                final_transaction_response_dict = transaction_response_instance.model_dump(by_alias=True)

                return {
                    'success': True,
                    'newBalance': updated_user.wallet.balance,
                    'transaction': final_transaction_response_dict 
                }

            except HTTPException as http_exc:
                 await session.abort_transaction()
                 raise http_exc
            except Exception as err:
                await session.abort_transaction()
                logger.error(f'Ошибка при списании средств: {err}', exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))


@app.get('/api/plans', response_model=List[SubscriptionPlanResponse])
async def get_all_plans():
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

@app.get('/api/plans/{planId}')
async def get_plan_by_id(planId: PydanticObjectId):
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

@app.post('/api/subscriptions/purchase', response_model=PurchaseSubscriptionResponse)
async def purchase_subscription(
    request_data: PurchaseSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    if motor_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database unavailable"
        )

    client = motor_client
    async with await client.start_session() as session:
        try:
            async with session.start_transaction():
                # Получаем пользователя и план
                user = await User.get(current_user.id, session=session)
                plan = await SubscriptionPlan.get(request_data.planId, session=session)
                
                if not user or not plan:
                    raise HTTPException(status_code=404, detail="User or plan not found")

                now = datetime.now(timezone.utc)
                
                # Обработка бесплатного плана
                if plan.price == 0:
                    subscription_data = CurrentSubscriptionEmbedded(
                        planId=plan.id,
                        startDate=now,
                        endDate=None,
                        isActive=True,
                        autoRenew=False,
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
                    
                    user.currentSubscription = subscription_data
                    await user.save(session=session)
                    
                    return PurchaseSubscriptionResponse(
                        success=True,
                        subscription=SubscriptionHistoryResponse(
                            id=str(user.id),  # Временное значение, нужно создать реальную запись
                            userId=user.id,
                            planId=plan.id,
                            startDate=now,
                            endDate=None,
                            isActive=True,
                            autoRenew=False,
                            changedByAdmin=False,
                            plan=SubscriptionPlanResponse(
                                id=str(plan.id),
                                name=plan.name,
                                price=plan.price,
                                renewalPeriod=plan.renewalPeriod,
                                features=plan.features,
                                createdAt=plan.createdAt,
                                updatedAt=plan.updatedAt
                            )
                        ),
                        newBalance=user.wallet.balance,
                        paymentRequired=False,
                        requiredAmount=0
                    )

                # Проверка баланса для платных планов
                if user.wallet.balance < plan.price:
                    return PurchaseSubscriptionResponse(
                        success=False,
                        paymentRequired=True,
                        requiredAmount=plan.price - user.wallet.balance,
                        newBalance=user.wallet.balance
                    )
                
                # Создаем транзакцию
                transaction = Transaction(
                    userId=user.id,
                    amount=-plan.price,
                    type='subscription',
                    status='completed',
                    description=f"Оплата подписки {plan.name}",
                    paymentMethod='balance',
                    currency='RUB',
                    metadata={  # Добавляем обязательное поле metadata
                        "planId": str(plan.id),
                        "planName": plan.name,
                        "type": "subscription_payment"
                    },
                    date=now,
                    createdAt=now,
                    updatedAt=now
                )
                await transaction.insert(session=session)

                # Обновляем баланс пользователя
                user.wallet.balance -= plan.price
                user.wallet.transactionIds.append(transaction.id)

                # Создаем запись в истории подписок
                renewal_days = plan.renewalPeriod or 30
                end_date = now + timedelta(days=renewal_days)
                
                subscription_history = SubscriptionHistory(
                    userId=user.id,
                    planId=plan.id,
                    startDate=now,
                    endDate=end_date,
                    isActive=True,
                    autoRenew=True,
                    changedByAdmin=False,
                    adminNote="Покупка через баланс",
                    createdAt=now,
                    updatedAt=now
                )
                await subscription_history.insert(session=session)

                # Обновляем текущую подписку пользователя
                user.currentSubscription = CurrentSubscriptionEmbedded(
                    planId=plan.id,
                    startDate=now,
                    endDate=end_date,
                    isActive=True,
                    autoRenew=True,
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

                # Формируем ответ
                response = PurchaseSubscriptionResponse(
                    success=True,
                    subscription=SubscriptionHistoryResponse(
                        id=str(subscription_history.id),
                        userId=user.id,
                        planId=plan.id,
                        startDate=now,
                        endDate=end_date,
                        isActive=True,
                        autoRenew=True,
                        changedByAdmin=False,
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
                    ),
                    newBalance=user.wallet.balance,
                    transaction=TransactionResponse(
                        id=str(transaction.id),
                        userId=user.id,
                        amount=transaction.amount,
                        type=transaction.type,
                        status=transaction.status,
                        description=transaction.description,
                        paymentMethod=transaction.paymentMethod,
                        currency=transaction.currency,
                        metadata=transaction.metadata,  # Добавляем metadata
                        date=transaction.date,
                        createdAt=transaction.createdAt,
                        updatedAt=transaction.updatedAt
                    ),
                    paymentRequired=False,
                    requiredAmount=0
                )

                await session.commit_transaction()
                return response

        except HTTPException as http_exc:
            if session.in_transaction:
                await session.abort_transaction()
            raise http_exc
        except Exception as err:
            logger.error(f"Subscription purchase error: {str(err)}", exc_info=True)
            if session.in_transaction:
                await session.abort_transaction()
            raise HTTPException(
                status_code=500,
                detail="Internal server error during subscription purchase"
            )
              
@app.get('/api/subscriptions/current')
async def get_current_subscription(current_user: User = Depends(get_current_user)):
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
        


@app.get('/api/admin/check')
async def admin_check(admin_user: User = Depends(get_admin_user)):
    return {"isAuthenticated": True}


@app.post('/api/admin/login')
async def admin_login(request_data: LoginUserRequest, request: Request):
    try:
        admin = await User.find_one({"email": request_data.email, "role": "admin"})
        if not admin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверные учетные данные или недостаточно прав')

        is_match = bcrypt.checkpw(request_data.password.encode('utf-8'), admin.password.encode('utf-8'))
        if not is_match:
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверные учетные данные')

        tokens = generate_tokens(admin)
        admin_agent = request.headers.get('user-agent', 'Unknown')
        refresh_token_data = RefreshTokenEmbedded(token=tokens['refreshToken'], userAgent=admin_agent)

        await User.find_one(User.id == admin.id).update({"$push": {'refreshTokens': refresh_token_data}})

        return {
            'success': True,
            'accessToken': tokens['accessToken'],
            'refreshToken': tokens['refreshToken'],
            'admin': {
                'id': str(admin.id),
                'email': admin.email,
                'role': admin.role
            }
        }

    except Exception as err:
        logger.error(f'Ошибка при логине администратора: {err}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Ошибка сервера при логине администратора')


@app.post('/api/admin/refresh-token')
async def admin_refresh_token(request_data: RefreshTokenRequest, request: Request):
    try:
        payload = jwt.decode(request_data.refreshToken, REFRESH_KEY, algorithms=[JWT_ALGORITHM])

        user_id: str = payload.get("userId")
        role: str = payload.get("role")

        if user_id is None or role != 'admin':
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверный refresh токен (нет userId или роль не admin)')

        admin = await User.find_one({"_id": PydanticObjectId(user_id), "role": "admin", 'refreshTokens.token': request_data.refreshToken})

        if not admin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Недействительный или уже использованный refresh токен')

        tokens = generate_tokens(admin)
        admin_agent = request.headers.get('user-agent', 'Unknown')
        new_refresh_token_data = RefreshTokenEmbedded(token=tokens['refreshToken'], userAgent=admin_agent)

        await User.find_one(User.id == admin.id).update(
            {"$pull": {'refreshTokens': {'token': request_data.refreshToken}}}
        )

        await User.find_one(User.id == admin.id).update(
            {"$push": {'refreshTokens': new_refresh_token_data}}
        )

        return {
            'success': True,
            'accessToken': tokens['accessToken'],
            'refreshToken': tokens['refreshToken']
        }

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверный или просроченный refresh токен')
    except Exception as err:
        logger.error(f'Ошибка при обновлении refresh токена администратора: {err}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Ошибка сервера при обновлении refresh токена')


@app.post('/api/admin/logout')
async def admin_logout(request_data: RefreshTokenRequest):
    try:
        if not request_data.refreshToken:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Refresh token is required')

        update_result = await User.find_one(
            {"role": "admin", 'refreshTokens.token': request_data.refreshToken}
        ).update({"$pull": {'refreshTokens': {'token': request_data.refreshToken}}})

        if update_result.modified_count == 0:
             user_with_token = await User.find_one({'refreshTokens.token': request_data.refreshToken})
             if not user_with_token:
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Refresh токен не найден или уже недействителен')

        return {
            "success": True,
            "message": "Logout successful"
        }

    except Exception as err:
        logger.error('Admin logout error:', err, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Ошибка сервера при выходе администратора')


@app.get('/api/admin/users')
async def get_admin_users(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=0),
    search: str = Query('', alias='search')
):
    try:
        skip = (page - 1) * limit

        query = {}
        if search:
            query['$or'] = [
                {'email': {'$regex': search, '$options': 'i'}},
                {'username': {'$regex': search, '$options': 'i'}}
            ]

        total = await User.find(query).count()
        
        pipeline = [
            {"$match": query},
            {"$skip": skip} if limit > 0 else {"$match": query},
            {"$limit": limit} if limit > 0 else {"$match": query},
            {"$lookup": {
                "from": "subscriptionplans",
                "localField": "currentSubscription.planId",
                "foreignField": "_id",
                "as": "currentSubscription.plan"
            }},
            {"$addFields": {
                "currentSubscription.plan": {"$arrayElemAt": ["$currentSubscription.plan", 0]},
                "wallet": {
                    "$ifNull": ["$wallet", {"balance": 0, "transactions": []}]
                }
            }},
            {"$project": {
                "_id": 1,
                "username": 1,
                "email": 1,
                "currentSubscription": 1,
                "wallet.balance": 1,
                "createdAt": 1
            }}
        ]

        users_cursor = User.aggregate(pipeline)
        users_list = await users_cursor.to_list()

        populated_users = []
        for user in users_list:
            user_data = {
                "_id": str(user["_id"]),
                "username": user.get("username"),
                "email": user.get("email"),
                "wallet": {
                    "balance": user.get("wallet", {}).get("balance", 0)
                },
                "currentSubscription": None
            }

            if user.get("currentSubscription"):
                sub_data = user["currentSubscription"]
                user_data["currentSubscription"] = {
                    "planId": str(sub_data.get("planId")),
                    "startDate": sub_data.get("startDate"),
                    "endDate": sub_data.get("endDate"),
                    "isActive": sub_data.get("isActive", False),
                    "autoRenew": sub_data.get("autoRenew", False),
                    "plan": None
                }

                if sub_data.get("plan"):
                    user_data["currentSubscription"]["plan"] = {
                        "_id": str(sub_data["plan"]["_id"]),
                        "name": sub_data["plan"].get("name"),
                        "price": sub_data["plan"].get("price"),
                        "features": sub_data["plan"].get("features", [])
                    }

            populated_users.append(user_data)

        pages = math.ceil(total / limit) if limit > 0 else (1 if total > 0 else 0)

        return {
            'success': True,
            'users': populated_users,
            'total': total,
            'page': page,
            'pages': pages
        }

    except Exception as err:
        logger.error(f'Ошибка при получении списка пользователей: {err}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Ошибка сервера при получении списка пользователей'
        )

@app.put('/api/admin/user/change/{userId}')
async def admin_change_user(
    userId: PydanticObjectId,
    request_data: AdminChangeUserRequest,
    request: Request,
    admin_user: User = Depends(get_admin_user)
):
    if motor_client is None:
        logger.error("MongoDB client not initialized")
        raise HTTPException(status_code=500, detail="Database not available")

    client = motor_client
    async with await client.start_session() as session:
        async with session.start_transaction():
            try:
                user = await User.get(userId, session=session)
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")

                old_data = user.model_dump()
                update_fields = {}
                changes = {}

                if request_data.username is not None and request_data.username != user.username:
                    if len(request_data.username) < 1:
                        raise HTTPException(status_code=400, detail="Username too short")
                    update_fields['username'] = request_data.username
                    changes['username'] = {'old': user.username, 'new': request_data.username}

                if request_data.email is not None and request_data.email != user.email:
                    try:
                        from pydantic import EmailStr
                        class EmailCheck(BaseModel):
                            email: EmailStr

                        EmailCheck(email=request_data.email)

                        existing_user = await User.find_one(
                            {"email": request_data.email, "_id": {"$ne": userId}},
                            session=session
                        )
                        if existing_user:
                            raise HTTPException(status_code=400, detail="Email already in use")
                        
                        update_fields['email'] = request_data.email
                        changes['email'] = {'old': user.email, 'new': request_data.email}
                    except ValueError as e:
                        raise HTTPException(status_code=400, detail="Invalid email format")

                if request_data.wallet is not None:
                    try:
                        new_balance = float(request_data.wallet.get('balance', user.wallet.balance))
                        if new_balance != user.wallet.balance:
                            update_fields['wallet.balance'] = new_balance
                            changes['wallet.balance'] = {
                                'old': user.wallet.balance,
                                'new': new_balance
                            }
                    except (TypeError, ValueError):
                        raise HTTPException(status_code=400, detail="Invalid balance value")

                if request_data.currentSubscription is not None:
                    sub_data = request_data.currentSubscription
                    new_subscription = {}

                    if 'planId' in sub_data and sub_data['planId']:
                        try:
                            plan_id = PydanticObjectId(sub_data['planId'])
                            plan = await SubscriptionPlan.get(plan_id, session=session)
                            if not plan:
                                raise HTTPException(status_code=404, detail="Subscription plan not found")
                            
                            new_subscription['planId'] = plan_id
                        except:
                            raise HTTPException(status_code=400, detail="Invalid planId format")

                    for field in ['startDate', 'endDate']:
                        if field in sub_data and sub_data[field]:
                            try:
                                if isinstance(sub_data[field], str):
                                    dt = datetime.fromisoformat(sub_data[field].replace("Z", "+00:00"))
                                else:
                                    dt = sub_data[field]
                                new_subscription[field] = dt
                            except ValueError:
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"Invalid {field} format"
                                )

                    for field in ['isActive', 'autoRenew', 'adminNote']:
                        if field in sub_data and sub_data[field] is not None:
                            new_subscription[field] = sub_data[field]

                    if new_subscription:
                        update_fields['currentSubscription'] = new_subscription
                        changes['currentSubscription'] = {
                            'old': user.currentSubscription,
                            'new': new_subscription
                        }

                if update_fields:
                    await User.find_one({"_id": userId}).update(
                        {"$set": update_fields},
                        session=session
                    )
                    updated_user = await User.get(userId, session=session)

                    await log_admin_action(
                        admin_user,
                        request,
                        "update",
                        "User",
                        userId,
                        changes,
                        f"Admin {admin_user.email} updated user {userId}"
                    )

                await session.commit_transaction()
                
                user_data = updated_user.model_dump(by_alias=True)
                user_data['_id'] = str(user_data['_id'])
                
                if user_data.get('currentSubscription') and user_data['currentSubscription'].get('planId'):
                    user_data['currentSubscription']['planId'] = str(user_data['currentSubscription']['planId'])
                
                return {
                    "success": True,
                    "user": user_data
                }

            except HTTPException as http_exc:
                await session.abort_transaction()
                raise http_exc
            except Exception as e:
                await session.abort_transaction()
                logger.error(f"Error updating user: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail="Internal server error")

@app.put('/api/admin/plans/change/{planId}')
async def admin_change_plan(
    planId: PydanticObjectId,
    request_data: AdminChangePlanRequest,
    request: Request,
    admin_user: User = Depends(get_admin_user)
):
    if motor_client is None:
        logger.error("MongoDB client not initialized")
        raise HTTPException(status_code=500, detail="Database not available")

    client = motor_client
    async with await client.start_session() as session:
        async with session.start_transaction():
            try:

                plan = await SubscriptionPlan.get(planId, session=session)
                if not plan:
                    raise HTTPException(status_code=404, detail="Subscription plan not found")

                old_data = plan.model_dump()
                update_fields = {}
                changes = {}


                if request_data.name is not None and request_data.name != plan.name:
                    if len(request_data.name) < 1:
                        raise HTTPException(status_code=400, detail="Plan name too short")
                    update_fields['name'] = request_data.name
                    changes['name'] = {'old': plan.name, 'new': request_data.name}


                if request_data.price is not None and request_data.price != plan.price:
                    if request_data.price < 0:
                        raise HTTPException(status_code=400, detail="Price cannot be negative")
                    update_fields['price'] = request_data.price
                    changes['price'] = {'old': plan.price, 'new': request_data.price}

   
                if request_data.renewalPeriod is not None and request_data.renewalPeriod != plan.renewalPeriod:
                    if request_data.renewalPeriod < 1:
                        raise HTTPException(status_code=400, detail="Renewal period must be at least 1 day")
                    update_fields['renewalPeriod'] = request_data.renewalPeriod
                    changes['renewalPeriod'] = {'old': plan.renewalPeriod, 'new': request_data.renewalPeriod}

        
                if request_data.features is not None and request_data.features != plan.features:
                    if not isinstance(request_data.features, list):
                        raise HTTPException(status_code=400, detail="Features must be a list")
                    update_fields['features'] = request_data.features
                    changes['features'] = {'old': plan.features, 'new': request_data.features}

         
                if update_fields:
                 
                    update_fields['updatedAt'] = datetime.now(timezone.utc)
                    
                    await SubscriptionPlan.find_one({"_id": planId}).update(
                        {"$set": update_fields},
                        session=session
                    )
                    
     
                    updated_plan = await SubscriptionPlan.get(planId, session=session)
                    
           
                    await log_admin_action(
                        admin_user,
                        request,
                        "update",
                        "SubscriptionPlan",
                        planId,
                        changes,
                        f"Admin {admin_user.email} updated subscription plan {planId}"
                    )

                await session.commit_transaction()
                
        
                plan_data = updated_plan.model_dump(by_alias=True)
                plan_data['_id'] = str(plan_data['_id'])
                
                return {
                    "success": True,
                    "plan": plan_data
                }

            except HTTPException as http_exc:
                await session.abort_transaction()
                raise http_exc
            except DuplicateKeyError:
                await session.abort_transaction()
                raise HTTPException(
                    status_code=400,
                    detail="Subscription plan with this name already exists"
                )
            except Exception as e:
                await session.abort_transaction()
                logger.error(f"Error updating subscription plan: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error"
                )


@app.post('/api/admin/plans/create')
async def admin_create_plan(
    request_data: AdminChangePlanRequest,
    request: Request,
    admin_user: User = Depends(get_admin_user)
):
    if motor_client is None:
        logger.error("MongoDB client not initialized")
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        if not request_data.name:
            raise HTTPException(status_code=400, detail="Plan name is required")
        if request_data.price is None:
            raise HTTPException(status_code=400, detail="Price is required")
        if request_data.renewalPeriod is None:
            raise HTTPException(status_code=400, detail="Renewal period is required")

        existing_plan = await SubscriptionPlan.find_one(
            SubscriptionPlan.name == request_data.name
        )
        if existing_plan:
            raise HTTPException(
                status_code=400,
                detail="Plan with this name already exists"
            )

        new_plan = SubscriptionPlan(
            name=request_data.name,
            price=request_data.price,
            renewalPeriod=request_data.renewalPeriod,
            features=request_data.features or []
        )

        await new_plan.insert()

        await log_admin_action(
            admin_user,
            request,
            "create",
            "SubscriptionPlan",
            new_plan.id,
            None,
            f"Admin {admin_user.email} created new subscription plan: {request_data.name}"
        )

        plan_data = new_plan.model_dump(by_alias=True)
        plan_data['_id'] = str(plan_data['_id'])
        
        return {
            "success": True,
            "message": "Тарифный план успешно создан",
            "plan": plan_data
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error creating subscription plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
        
@app.delete('/api/admin/plans/delete/{planId}')
async def admin_delete_plan(
    planId: PydanticObjectId,
    request: Request,
    admin_user: User = Depends(get_admin_user)
):
    if motor_client is None:
        logger.error("MongoDB client not initialized")
        raise HTTPException(status_code=500, detail="Database not available")

    client = motor_client
    async with await client.start_session() as session:
        async with session.start_transaction():
            try:
                plan_to_delete = await SubscriptionPlan.get(planId, session=session)
                if not plan_to_delete:
                    await session.abort_transaction()
                    raise HTTPException(status_code=404, detail="Subscription plan not found")

                users_with_plan = await User.find_one(
                    {"currentSubscription.planId": planId},
                    session=session
                )
                
                if users_with_plan:
                    await session.abort_transaction()
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot delete plan - it's currently used by users"
                    )

                await plan_to_delete.delete(session=session)

                await log_admin_action(
                    admin_user,
                    request,
                    "delete",
                    "SubscriptionPlan",
                    planId,
                    None,
                    f"Admin {admin_user.email} deleted subscription plan: {plan_to_delete.name}"
                )

                await session.commit_transaction()

                return {
                    "success": True,
                    "message": "Тарифный план успешно удален"
                }

            except HTTPException as http_exc:
                await session.abort_transaction()
                raise http_exc
            except Exception as e:
                await session.abort_transaction()
                logger.error(f"Error deleting subscription plan: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error"
                )

@app.on_event("startup")
async def startup_event():
    """Runs before the application starts."""
    await init_db()


@app.get("/")
async def read_root():
    return {"message": "Сервер FastAPI запущен!"}


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Сервер запущен на порту {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=int(PORT))