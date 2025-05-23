from __future__ import annotations
from backend.core.config import (
    logger,
    PORT,
    ALLOWED_ORIGINS,
    PUBLIC_DIR,
    AVATAR_UPLOAD_DIR,
    JWT_SECRET_KEY, # <-- Добавьте это
    REFRESH_SECRET_KEY, # <-- Добавьте это (если используется для токенов обновления)
    JWT_ALGORITHM # <-- Добавьте это
)
from backend.core.database import init_db
from backend.core.tasks import init_scheduler
from backend.core.dependencies import get_current_user, get_admin_user, log_admin_action, generate_tokens
from backend.core.database import get_motor_client

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

from backend.models import (
    User,
    SubscriptionPlan,
    SubscriptionHistory,
    Transaction,
    AdminAction
)
from backend.models.embedded import (
    RefreshTokenEmbedded,
    CurrentSubscriptionEmbedded,
    SubscriptionHistoryEmbedded,
    WalletEmbedded,
    NotificationsEmbedded
)
from backend.schemas import (
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

from backend.routers.user_router import router as user_router
from backend.routers.wallet_router import router as wallet_router
from backend.routers.subscription_router import router as subscription_router
from backend.routers.admin_auth_router import router as admin_auth_router
from backend.routers.admin_user_router import router as admin_user_router
from backend.routers.admin_plan_router import router as admin_plan_router


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "x-access-token"],
)
app.json_encoders = {
    PydanticObjectId: str
}


SubscriptionPlanResponse.model_rebuild()
SubscriptionHistoryEmbedded.model_rebuild()
CurrentSubscriptionEmbedded.model_rebuild()
WalletEmbedded.model_rebuild()
NotificationsEmbedded.model_rebuild()
RefreshTokenEmbedded.model_rebuild()
TransactionResponse.model_rebuild()
AdminActionResponse.model_rebuild()
UserResponseBase.model_rebuild()







app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="static")

app.include_router(user_router)
app.include_router(wallet_router)
app.include_router(subscription_router)
app.include_router(admin_auth_router)
app.include_router(admin_user_router)
app.include_router(admin_plan_router)

        


@app.on_event("startup")
async def startup_event():
    """Runs before the application starts."""
    logger.info("Starting up application...")
    
    try:
        await init_db() # Только вызов функции инициализации базы данных
        logger.info("Database initialized successfully.")
        await init_scheduler() # <--- НЕ ЗАБУДЬТЕ ВЕРНУТЬ ЭТОТ ВЫЗОВ!
        logger.info("Scheduler initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize application: {e}", exc_info=True)
        # В случае критической ошибки на старте, FastAPI сам не запустит сервер.
        raise # Перевыбрасываем исключение, чтобы оно было видно


@app.get("/")
async def read_root():
    return {"message": "Сервер FastAPI запущен!"}


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Сервер запущен на порту {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=int(PORT))