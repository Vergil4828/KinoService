from typing import AsyncGenerator, Callable, Optional, Any, Awaitable

import httpx

from tests.api.wallet.wallet_client import WalletClient
import pytest
import asyncio
import os
import shutil
import uuid
from tests.api.user.user_client import UserClient
from tests.data.API_User.user_test_data import CreateUserData
from motor.motor_asyncio import AsyncIOMotorClient
from backend.core.redis_client import get_redis_client, init_redis, close_redis
from bson import ObjectId
import pytest_asyncio


UserCreationFunction = Callable[
    [Optional[dict[str, Any]]],
    Awaitable[tuple[dict[str, Any], httpx.Response, str]],
]
UserCleanFunction = Callable[[str], Awaitable[None]]


@pytest.fixture(scope="session")
def api_client_user() -> UserClient:
    return UserClient()


@pytest.fixture(scope="session")
def api_client_wallet() -> WalletClient:
    return WalletClient()


async def clean_cache_redis(delete_cache: str) -> None:
    await init_redis()
    redis_client = get_redis_client()
    if redis_client:
        await redis_client.delete(delete_cache)
    await close_redis()


@pytest_asyncio.fixture(scope="class")
async def registered_user_in_db_per_class(
    api_client_user: UserClient, request: Any
) -> AsyncGenerator[
    UserCreationFunction,
    None,
]:
    registered_user_data = None

    async def create_user(
        user_data: Optional[dict[str, Any]] = None,
    ) -> tuple[dict[str, Any], httpx.Response, str]:
        nonlocal registered_user_data
        if registered_user_data:
            return (
                registered_user_data["user_data"],
                registered_user_data["response_data"],
                registered_user_data["accessToken"],
            )
        if not user_data:
            user_data = CreateUserData.base_user_data.copy()
            user_data["email"] = f"user_{uuid.uuid4()}@example.com"
            user_data["username"] = f"user_{uuid.uuid4()}"

        response = await api_client_user.register_user(user_data)
        assert response.status_code == 201
        accessToken = response.json()["accessToken"]
        registered_user_data = {
            "user_data": user_data,
            "response_data": response,
            "accessToken": accessToken,
        }
        return user_data, response, accessToken

    yield create_user

    if registered_user_data:
        client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        user_id = registered_user_data["response_data"].json()["user"]["id"]
        await clean_cache_redis(f"refresh_token:{user_id}")
        await clean_cache_redis(f"wallet_data:{user_id}")

        try:
            db = client["8_films"]
            user_id_obj = ObjectId(user_id)
            await db.users.delete_one({"_id": user_id_obj})
        finally:
            client.close()
        test_class_name = request.cls.__name__
        if "TestUploadAvatarPositive" in test_class_name:
            user_id = registered_user_data["response_data"].json()["user"]["id"]
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..")
            )
            avatars_dir = os.path.join(project_root, "public", "uploads", "avatars")
            avatar_path = os.path.join(avatars_dir, user_id)
            if os.path.exists(avatar_path):
                shutil.rmtree(avatar_path)


@pytest_asyncio.fixture(scope="function")
async def registered_user_in_db_per_function(
    api_client_user: UserClient, request: Any
) -> AsyncGenerator[
    UserCreationFunction,
    None,
]:
    registered_user_data = None

    async def create_user(
        user_data: Optional[dict[str, Any]] = None,
    ) -> tuple[dict[str, Any], httpx.Response, str]:
        nonlocal registered_user_data
        if registered_user_data:
            return (
                registered_user_data["user_data"],
                registered_user_data["response_data"],
                registered_user_data["accessToken"],
            )
        if not user_data:
            user_data = CreateUserData.base_user_data.copy()
            user_data["email"] = f"user_{uuid.uuid4()}@example.com"
            user_data["username"] = f"user_{uuid.uuid4()}"

        response = await api_client_user.register_user(user_data)
        assert response.status_code == 201
        accessToken = response.json()["accessToken"]
        registered_user_data = {
            "user_data": user_data,
            "response_data": response,
            "accessToken": accessToken,
        }
        return user_data, response, accessToken

    yield create_user

    if registered_user_data:
        client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        user_id = registered_user_data["response_data"].json()["user"]["id"]

        await clean_cache_redis(f"refresh_token:{user_id}")
        await clean_cache_redis(f"wallet_data:{user_id}")

        try:
            db = client["8_films"]
            user_id_obj = ObjectId(user_id)
            await db.users.delete_one({"_id": user_id_obj})
        finally:
            client.close()

        test_class_name = request.cls.__name__
        if "TestUploadAvatarPositive" in test_class_name:
            user_id = registered_user_data["response_data"].json()["user"]["id"]
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..")
            )
            avatars_dir = os.path.join(project_root, "public", "uploads", "avatars")
            avatar_path = os.path.join(avatars_dir, user_id)
            if os.path.exists(avatar_path):
                shutil.rmtree(avatar_path)


# Переписать (т.к это не фикстура, а просто удаление)
# Добавить нормальную фикстуру, которая в начале будет собирать айди и статус код
# а после теста удалять юзеров
@pytest_asyncio.fixture(scope="function")
async def clean_user_now() -> UserCleanFunction:
    async def delete_user(user_id: str) -> None:

        await clean_cache_redis(f"refresh_token:{user_id}")
        client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        db = client["8_films"]
        try:
            user_id_obj = ObjectId(user_id)
            await db.users.delete_one({"_id": user_id_obj})

        finally:
            client.close()

    return delete_user


@pytest_asyncio.fixture(scope="function")
async def prepare_db_and_redis_without_basic_plan() -> AsyncGenerator[None, None]:
    basic_plan = None
    basic_plan_redis = None
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client["8_films"]

    basic_plan = await db.subscriptionplans.find_one({"price": 0})
    if basic_plan:
        await db.subscriptionplans.delete_one({"price": 0})

    await init_redis()
    redis_client = get_redis_client()
    if redis_client:
        basic_plan_redis = await redis_client.get("plan:Базовый")
        await redis_client.delete("plan:Базовый")

    yield

    if basic_plan:
        await db.subscriptionplans.insert_one(basic_plan)
    if basic_plan_redis:
        await redis_client.set("plan:Базовый", basic_plan_redis)
    client.close()
    await close_redis()
    await asyncio.sleep(1)
