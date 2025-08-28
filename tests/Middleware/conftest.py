import pytest, asyncio, os, shutil, uuid
from tests.API.User.user_client import UserClient
from tests.API.Wallet.wallet_client import WalletClient
from tests.data.API_User.user_test_data import CreateUserData
from motor.motor_asyncio import AsyncIOMotorClient
from backend.core.redis_client import get_redis_client, init_redis, close_redis
from bson import ObjectId
import pytest_asyncio


async def clean_user_token(user_id):
    await init_redis()
    redis_client = get_redis_client()
    if redis_client:
        await redis_client.delete(f"refresh_token:{user_id}")
    await close_redis()


@pytest.fixture(scope="session")
def api_client_user():
    return UserClient()


@pytest.fixture(scope="session")
def api_client_wallet():
    return WalletClient()


@pytest_asyncio.fixture(scope="class")
async def registered_user_in_db_per_class(api_client_user, request):
    registered_user_data = None

    async def create_user(user_data):
        nonlocal registered_user_data
        if registered_user_data:
            return (
                registered_user_data["user_data"],
                registered_user_data["response_data"],
            )
        if not user_data:
            user_data = CreateUserData.base_user_data.copy()
            user_data["email"] = f"user_{uuid.uuid4()}@example.com"
            user_data["username"] = f"user_{uuid.uuid4()}"

        response = await api_client_user.register_user(user_data)
        assert response.status_code == 201

        registered_user_data = {"user_data": user_data, "response_data": response}
        return user_data, response

    yield create_user

    if registered_user_data:
        client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        user_id = registered_user_data["response_data"].json()["user"]["id"]
        await clean_user_token(user_id)

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
                os.path.join(os.path.dirname(__file__), "..", "..", "..")
            )
            avatars_dir = os.path.join(project_root, "public", "uploads", "avatars")
            avatar_path = os.path.join(avatars_dir, user_id)
            if os.path.exists(avatar_path):
                shutil.rmtree(avatar_path)


@pytest_asyncio.fixture(scope="function")
async def registered_user_in_db_per_function(api_client_user, request):
    registered_user_data = None

    async def create_user(user_data):
        nonlocal registered_user_data
        if registered_user_data:
            return (
                registered_user_data["user_data"],
                registered_user_data["response_data"],
            )
        if not user_data:
            user_data = CreateUserData.base_user_data.copy()
            user_data["email"] = f"user_{uuid.uuid4()}@example.com"
            user_data["username"] = f"user_{uuid.uuid4()}"

        response = await api_client_user.register_user(user_data)
        assert response.status_code == 201

        registered_user_data = {"user_data": user_data, "response_data": response}
        return user_data, response

    yield create_user

    if registered_user_data:
        client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        user_id = registered_user_data["response_data"].json()["user"]["id"]
        await clean_user_token(user_id)

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
                os.path.join(os.path.dirname(__file__), "..", "..", "..")
            )
            avatars_dir = os.path.join(project_root, "public", "uploads", "avatars")
            avatar_path = os.path.join(avatars_dir, user_id)
            if os.path.exists(avatar_path):
                shutil.rmtree(avatar_path)


@pytest_asyncio.fixture(scope="function")
async def clean_user_now():
    async def delete_user(user_id):

        await clean_user_token(user_id)
        client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        db = client["8_films"]
        try:
            user_id_obj = ObjectId(user_id)
            await db.users.delete_one({"_id": user_id_obj})

        finally:
            client.close()

    return delete_user


@pytest_asyncio.fixture(scope="function")
async def prepare_db_without_basic_plan():
    basic_plan = None
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client["8_films"]

    basic_plan = await db.subscriptionplans.find_one({"price": 0})
    if basic_plan:
        await db.subscriptionplans.delete_one({"price": 0})

    yield

    if basic_plan:
        basic_plan.pop("_id", None)
        await db.subscriptionplans.insert_one(basic_plan)

    client.close()
    await asyncio.sleep(1)
