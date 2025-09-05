from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.core.config import logger

from backend.models.user import User
from backend.models.subscription import SubscriptionPlan, SubscriptionHistory

from backend.models.embedded.subscription import CurrentSubscriptionEmbedded

from backend.core.database import get_motor_client

scheduler: AsyncIOScheduler = None


async def init_scheduler():
    global scheduler

    await initSubscriptionPlans()

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            checkAndUpdateSubscriptions,
            "interval",
            minutes=1,
            id="checkAndUpdateSubscriptions",
        )
        scheduler.start()
        logger.info("Cron-задача для проверки подписок активирована")
    else:
        logger.info("Планировщик уже инициализирован.")


async def initSubscriptionPlans():
    try:
        client = get_motor_client()
        async with await client.start_session() as session:
            async with session.start_transaction():
                plans_count = await SubscriptionPlan.find(session=session).count()

                if plans_count > 0:
                    logger.info(
                        "Тарифные планы уже существуют, инициализация не требуется"
                    )
                    await session.commit_transaction()
                    return

                plans_data = [
                    {
                        "name": "Базовый",
                        "price": 0,
                        "renewalPeriod": 30,
                        "features": ["Full HD качество", "1 устройство", "С рекламой"],
                    },
                    {
                        "name": "Популярный",
                        "price": 899,
                        "renewalPeriod": 30,
                        "features": [
                            "4K Ultra HD + HDR",
                            "До 5 устройств",
                            "Без рекламы",
                            "Оффлайн просмотр",
                        ],
                    },
                    {
                        "name": "Премиум+",
                        "price": 1199,
                        "renewalPeriod": 30,
                        "features": [
                            "4K Ultra HD + HDR + Dolby Vision",
                            "До 7 устройств",
                            "Без рекламы + ранний доступ",
                            "Оффлайн-просмотр + эксклюзивы",
                        ],
                    },
                ]

                plan_documents = [SubscriptionPlan(**plan) for plan in plans_data]
                await SubscriptionPlan.insert_many(plan_documents, session=session)
                logger.info(
                    f"Тарифные планы успешно инициализированы: {len(plan_documents)} добавлено"
                )
                await session.commit_transaction()

    except Exception as e:
        if "session" in locals() and session.in_transaction:
            await session.abort_transaction()
        logger.error(f"Ошибка при инициализации тарифных планов: {e}", exc_info=True)


async def checkAndUpdateSubscriptions():
    try:
        client = get_motor_client()
    except RuntimeError as e:
        logger.error(
            f"Ошибка при проверки подписок: {e}. Задача пропущена.", exc_info=False
        )
        return

    async with await client.start_session() as session:
        async with session.start_transaction():
            try:
                now_utc = datetime.now(timezone.utc)
                logger.info(f"[{now_utc.isoformat()}] Запуск проверки подписок...")

                users_to_update = await User.find(
                    {
                        "currentSubscription.endDate": {"$lte": now_utc, "$ne": None},
                        "currentSubscription.isActive": True,
                    },
                    session=session,
                ).to_list()

                logger.info(
                    f"Найдено {len(users_to_update)} пользователей для обновления"
                )

                basic_plan = await SubscriptionPlan.find_one(
                    SubscriptionPlan.price == 0, session=session
                )
                if not basic_plan:
                    raise Exception("Базовый тарифный план не найден")

                for user in users_to_update:
                    if user.currentSubscription and user.currentSubscription.planId:
                        history_entry = SubscriptionHistory(
                            userId=user.id,
                            planId=user.currentSubscription.planId,
                            startDate=user.currentSubscription.startDate
                            or datetime.now(timezone.utc),
                            endDate=now_utc,
                            isActive=False,
                            autoRenew=user.currentSubscription.autoRenew,
                        )
                        await history_entry.insert(session=session)
                        logger.info(
                            f"История подписки пользователя {user.id} добавлена в \
                            отдельную коллекцию"
                        )

                    user.currentSubscription = CurrentSubscriptionEmbedded(
                        planId=basic_plan.id,
                        startDate=datetime.now(timezone.utc),
                        endDate=None,
                        isActive=True,
                        autoRenew=False,
                    )
                    await user.save(session=session)
                    logger.info(f"Пользователь {user.id} переведен на базовый тариф")

                await session.commit_transaction()
                logger.info("Проверка подписок завершена успешно")

            except Exception as error:
                await session.abort_transaction()
                logger.error(f"Ошибка при проверке подписок: {error}", exc_info=True)


async def shutdown_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Проверка подписок остановлена")
