import logging
from datetime import datetime, timezone, timedelta # Добавляем timedelta, если он используется для расчетов
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from beanie.odm.fields import PydanticObjectId # Обычно не нужен здесь напрямую

# Импортируем logger из config.py
from backend.core.config import logger

# Импортируем нужные модели Beanie Document
from backend.models.user import User
from backend.models.subscription import SubscriptionPlan, SubscriptionHistory

# Импортируем Embedded модели, если они нужны для создания экземпляров
from backend.models.embedded.subscription import CurrentSubscriptionEmbedded # Это BaseModel

# *** ИСПРАВЛЕНИЕ: Используем get_motor_client() вместо прямого импорта motor_client ***
from backend.core.database import get_motor_client 


# Глобальная переменная для планировщика (для возможности остановки)
scheduler: AsyncIOScheduler = None 

async def init_scheduler():
    """Инициализирует и запускает планировщик задач."""
    global scheduler # Объявляем, что будем изменять глобальную переменную

    # initSubscriptionPlans должен быть вызван ОДИН раз при запуске приложения,
    # а не как часть периодической задачи. Это должно быть в startup_event в main.py
    # или, если вы хотите, чтобы это выполнялось каждый раз при запуске нового процесса uvicorn,
    # то оставьте его здесь, но учтите, что он будет вызываться несколько раз.
    # Если он уже вызван в main.py, то здесь это избыточно.
    # Для целей этого примера, оставляем здесь, но имейте в виду.
    await initSubscriptionPlans()

    if scheduler is None: # Проверяем, чтобы не инициализировать дважды
        scheduler = AsyncIOScheduler()
        # id='checkAndUpdateSubscriptions' - хорошая практика для идентификации задачи
        scheduler.add_job(checkAndUpdateSubscriptions, 'interval', minutes=1, id='checkAndUpdateSubscriptions')
        scheduler.start()
        logger.info('Cron-задача для проверки подписок активирована')
    else:
        logger.info('Планировщик уже инициализирован.')


async def initSubscriptionPlans():
    logger.info("Проверка и инициализация тарифных планов...")
    try:
        client = get_motor_client()
        async with await client.start_session() as session:
            async with session.start_transaction():
                # ИСПРАВЛЕНИЕ: Передаем session в find(), затем вызываем count() на курсоре
                plans_count = await SubscriptionPlan.find(session=session).count()

                if plans_count > 0:
                    logger.info('Тарифные планы уже существуют, инициализация не требуется')
                    await session.commit_transaction()
                    return

                plans_data = [
                    {"name": "Базовый", "price": 0, "renewalPeriod": 30, "features": ["Full HD качество", "1 устройство", "С рекламой"]},
                    {"name": "Популярный", "price": 899, "renewalPeriod": 30, "features": ["4K Ultra HD + HDR", "До 5 устройств", "Без рекламы", "Оффлайн просмотр"]},
                    {"name": "Премиум+", "price": 1199, "renewalPeriod": 30, "features": ["4K Ultra HD + HDR + Dolby Vision", "До 7 устройств", "Без рекламы + ранний доступ", "Оффлайн-просмотр + эксклюзивы"]}
                ]

                plan_documents = [SubscriptionPlan(**plan) for plan in plans_data]
                await SubscriptionPlan.insert_many(plan_documents, session=session)
                logger.info(f'Тарифные планы успешно инициализированы: {len(plan_documents)} добавлено')
                await session.commit_transaction()

    except Exception as e:
        # Убедитесь, что abort_transaction вызывается только если транзакция была начата
        if 'session' in locals() and session.in_transaction: 
            await session.abort_transaction()
        logger.error(f'Ошибка при инициализации тарифных планов: {e}', exc_info=True)



async def checkAndUpdateSubscriptions():
    """
    Проверяет просроченные подписки и переводит пользователей на базовый план.
    Использует MongoDB транзакции.
    """
    # *** ИСПРАВЛЕНИЕ: Всегда получаем клиент через get_motor_client() ***
    try:
        client = get_motor_client()
    except RuntimeError as e:
        logger.error(f"Ошибка при проверки подписок: {e}. Задача пропущена.", exc_info=False)
        return

    async with await client.start_session() as session:
        async with session.start_transaction():
            try:
                now_utc = datetime.now(timezone.utc)
                logger.info(f"[{now_utc.isoformat()}] Запуск проверки подписок...")

                # *** ИСПРАВЛЕНИЕ: Передаем session в find() ***
                users_to_update = await User.find({
                    'currentSubscription.endDate': {
                        '$lte': now_utc,
                        '$ne': None
                    },
                    'currentSubscription.isActive': True
                }, session=session).to_list() # <--- УБИРАЕМ session=session ОТСЮДА!

                logger.info(f"Найдено {len(users_to_update)} пользователей для обновления")

                # *** ИСПРАВЛЕНИЕ: Передаем session в find_one() ***
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
                        # *** ИСПРАВЛЕНИЕ: Передаем session в insert() ***
                        await history_entry.insert(session=session)
                        logger.info(f"История подписки пользователя {user.id} добавлена в отдельную коллекцию")

                    user.currentSubscription = CurrentSubscriptionEmbedded(
                        planId=basic_plan.id,
                        startDate=datetime.now(timezone.utc),
                        endDate=None,
                        isActive=True,
                        autoRenew=False
                    )

                    # *** ИСПРАВЛЕНИЕ: Передаем session в save() ***
                    await user.save(session=session)
                    logger.info(f"Пользователь {user.id} переведен на базовый тариф")

                await session.commit_transaction()
                logger.info('Проверка подписок завершена успешно')

            except Exception as error:
                await session.abort_transaction()
                logger.error(f'Ошибка при проверке подписок: {error}', exc_info=True)

# Функция для остановки планировщика при завершении работы приложения
async def shutdown_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down.")