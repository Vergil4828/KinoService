import redis.asyncio as redis
from backend.core.config import REDIS_URL, logger
from backend.models import SubscriptionPlan

redis_client = None


async def init_redis():
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Успешное подключение к Redis")
    except Exception as e:
        logger.error(f"Ошибка подключения к Redis: {e}")
        raise


async def close_redis():
    if redis_client:
        await redis_client.close()
        logger.info("Соединение с Redis закрыто")


def get_redis_client():
    if not redis_client:
        logger.error("Клиент Redis не инициализирован. Вызовите init_redis.")
        raise RuntimeError("Клиент Redis не инициализирован")
    return redis_client


async def load_subscription_plans(redis_client_plan):
    if await redis_client_plan.get("subscription_plans_loaded"):
        return

    plans = await SubscriptionPlan.find_all().to_list()

    if not plans:
        return

    for plan in plans:
        plan_name = str(plan.name)
        await redis_client_plan.set(f"plan:{plan_name}", plan.model_dump_json())

    await redis_client_plan.set("subscription_plans_loaded", "true")


async def delete_redis_cache(redis_key):
    if redis_client:
        if await redis_client.exists(redis_key):
            await redis_client.delete(redis_key)
