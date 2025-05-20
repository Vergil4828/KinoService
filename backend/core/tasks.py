# backend/core/tasks.py
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from beanie.odm.fields import PydanticObjectId # Если нужно для Link или чего-то подобного

# Импортируем logger из config.py
from backend.core.config import logger

# Импортируем нужные модели Beanie Document
from backend.models.user import User
from backend.models.subscription import SubscriptionPlan, SubscriptionHistory

# Импортируем Embedded модели, если они нужны для создания экземпляров
from backend.models.embedded.subscription import CurrentSubscriptionEmbedded # Это BaseModel

# Если вам нужен доступ к motor_client для транзакций,
# то init_db должна его вернуть или сохранить где-то глобально.
# В нашем случае, мы сохраняем его в database.py, и если tasks.py нужен прямой доступ,
# то придется его импортировать или передавать.
# Однако, для Beanie-операций (find, save, insert), motor_client не нужен.
# Только для start_session/start_transaction.
from backend.core.database import motor_client # Импортируем глобальный клиент

async def init_scheduler():
    """Инициализирует и запускает планировщик задач."""
    # initSubscriptionPlans должен быть вызван ОДИН раз при запуске приложения,
    # а не как часть периодической задачи.
    await initSubscriptionPlans()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(checkAndUpdateSubscriptions, 'interval', minutes=1)
    scheduler.start()
    logger.info('Cron-задача для проверки подписок активирована')


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
    Проверяет просроченные подписки и переводит пользователей на базовый план.
    Использует MongoDB транзакции.
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