# backend/core/database.py
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document
from typing import List, Type, Optional

# Импортируем только нужные переменные из config.py
from backend.core.config import MONGO_URI, MONGO_DB_NAME, logger

# Импортируем все ваши Beanie Document модели
from backend.models.user import User
from backend.models.subscription import SubscriptionPlan, SubscriptionHistory
from backend.models.transaction import Transaction
from backend.models.admin_action import AdminAction
from backend.models.user_stats import UserStats

# Глобальная переменная для клиента Motor
motor_client: Optional[AsyncIOMotorClient] = None

async def init_db():
    """
    Инициализирует подключение к базе данных MongoDB с использованием Beanie.
    """
    global motor_client # Объявляем, что будем изменять глобальную переменную

    if not MONGO_URI or not MONGO_DB_NAME:
        logger.error("MONGO_URI или MONGO_DB_NAME не установлены. Проверьте ваш .env файл и backend/core/config.py.")
        # Выбрасываем исключение, чтобы приложение не запускалось без настроенной БД
        raise ValueError("Не удалось подключиться к базе данных: отсутствуют MONGO_URI или MONGO_DB_NAME.")

    logger.info("--- TEST LOG: init_db начала выполнение ---")
    logger.info("Попытка подключения к MongoDB...")

    try:
        motor_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)

        # Проверяем соединение с БД
        await motor_client.admin.command('ping')
        logger.info("Подключение к MongoDB успешно установлено")

        db_name = MONGO_DB_NAME # Используем импортированное имя БД из config.py

        logger.info(f"Подключение к базе данных: {db_name}")

        # Список всех моделей Beanie Document
        document_models: List[Type[Document]] = [
            User,
            SubscriptionPlan,
            SubscriptionHistory,
            UserStats,
            Transaction,
            AdminAction,
            # Добавьте сюда все остальные ваши Beanie.Document модели.
            # Помните: EmbeddedDocument, которые наследуются от BaseModel, сюда не добавляются!
        ]

        await init_beanie(database=motor_client[db_name], document_models=document_models)
        logger.info("Успешное подключение к MongoDB и инициализация Beanie")

    except Exception as e: # Ловим все исключения, чтобы не пропустить
        logger.error(f"Критическая ошибка подключения к базе данных или инициализации Beanie: {e}", exc_info=True)
        # В случае критической ошибки подключения, приложение не должно запускаться
        raise # Перевыбрасываем исключение, чтобы FastAPI его поймал и остановил стартап