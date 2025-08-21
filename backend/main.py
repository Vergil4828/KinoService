from __future__ import annotations
from backend.core.config import (
    logger,
    PORT,
    ALLOWED_ORIGINS,
    PUBLIC_DIR,
    AVATAR_UPLOAD_DIR,
    JWT_SECRET_KEY,
    REFRESH_SECRET_KEY,
    JWT_ALGORITHM,
)
from backend.core.database import init_db, get_motor_client
from backend.core.redis_client import (
    init_redis,
    close_redis,
    get_redis_client,
    load_subscription_plans,
)
from backend.core.tasks import init_scheduler
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import AsyncContextManager, Any
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import json
from beanie import PydanticObjectId
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.models import (
    User,
    SubscriptionPlan,
    SubscriptionHistory,
    Transaction,
    AdminAction,
)
from backend.models.embedded import (
    RefreshTokenEmbedded,
    CurrentSubscriptionEmbedded,
    SubscriptionHistoryEmbedded,
    WalletEmbedded,
    NotificationsEmbedded,
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
    AdminChangeUserRequest,
)

from backend.routers.user_router import router as user_router
from backend.routers.wallet_router import router as wallet_router
from backend.routers.subscription_router import router as subscription_router
from backend.routers.admin_auth_router import router as admin_auth_router
from backend.routers.admin_user_router import router as admin_user_router
from backend.routers.admin_plan_router import router as admin_plan_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncContextManager[None]:
    logger.info("Starting up application...")
    try:
        await init_db()
        logger.info("Database initialized successfully.")
        await init_redis()
        logger.info("Redis client initialized successfully.")
        await load_subscription_plans(get_redis_client())
        logger.info("Subscription plans loaded into Redis.")
        await init_scheduler()
        logger.info("Scheduler initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize application: {e}", exc_info=True)
        raise

    yield

    logger.info("Shutting down application...")
    await close_redis()
    logger.info("Redis client connection closed.")


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ALLOWED_ORIGINS
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "x-access-token"],
)
app.json_encoders = {PydanticObjectId: str}


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


@app.get("/")
async def read_root():
    return {"message": "Сервер FastAPI запущен!"}


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Сервер запущен на порту {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=int(PORT))
