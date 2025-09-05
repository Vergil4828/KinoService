from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document
from typing import List, Type, Optional
from backend.core.config import MONGO_URI, MONGO_DB_NAME, logger
from backend.models.user import User
from backend.models.subscription import SubscriptionPlan, SubscriptionHistory
from backend.models.transaction import Transaction
from backend.models.admin import AdminAction


motor_client: Optional[AsyncIOMotorClient] = None


async def init_db():
    global motor_client

    if not MONGO_URI or not MONGO_DB_NAME:
        logger.error(
            "MONGO_URI или MONGO_DB_NAME не установлены. \
             Проверьте ваш .env файл и backend/core/config.py."
        )

        raise ValueError(
            "Не удалось подключиться к базе данных: отсутствуют MONGO_URI или MONGO_DB_NAME."
        )

    logger.info("Попытка подключения к MongoDB...")

    try:
        motor_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)

        await motor_client.admin.command("ping")
        logger.info("Подключение к MongoDB успешно установлено")

        db_name = MONGO_DB_NAME

        logger.info(f"Подключение к базе данных: {db_name}")

        document_models: List[Type[Document]] = [
            User,
            SubscriptionPlan,
            SubscriptionHistory,
            Transaction,
            AdminAction,
        ]

        await init_beanie(
            database=motor_client[db_name], document_models=document_models
        )
        logger.info("Успешное подключение к MongoDB и инициализация Beanie")

    except Exception as e:
        logger.error(
            f"Критическая ошибка подключения к базе данных или инициализации Beanie: {e}",
            exc_info=True,
        )
        raise


def get_motor_client() -> AsyncIOMotorClient:
    if motor_client is None:

        logger.error("Motor client не инициализирован. Вызовите init_db сначала.")
        raise RuntimeError("Мотор клиент не инициализирован")
    return motor_client
