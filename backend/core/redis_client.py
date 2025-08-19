import redis.asyncio as redis
from backend.core.config import REDIS_URL, logger

redis_client = None


async def init_redis():
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL)
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
