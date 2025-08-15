import pytest, asyncio, os, shutil, uuid
from tests.API.User.user_client import UserClient
from tests.data.API_User.user_test_data import CreateUserData
from motor.motor_asyncio import AsyncIOMotorClient


@pytest.fixture(scope="session")
def api_client_user():
    return UserClient()


@pytest.fixture(scope="class")
def registered_user_in_db_per_class(api_client_user, request):
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
        from pymongo import MongoClient

        client = MongoClient("mongodb://localhost:27018/?directConnection=true")
        try:
            db = client["8_films"]
            db.users.delete_one({"email": registered_user_data["user_data"]["email"]})
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


@pytest.fixture(scope="function")
def registered_user_in_db_per_function(api_client_user, request):
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
        from pymongo import MongoClient

        client = MongoClient("mongodb://localhost:27018/?directConnection=true")
        try:
            db = client["8_films"]
            db.users.delete_one({"email": registered_user_data["user_data"]["email"]})
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


@pytest.fixture(scope="class")
def clean_all_users():
    emails_to_clean = []

    async def cleanup_user(email):
        emails_to_clean.append(email)

    yield cleanup_user

    if emails_to_clean:
        client = AsyncIOMotorClient("mongodb://localhost:27018/?directConnection=true")
        db = client["8_films"]

        async def run_cleanup():
            for email in emails_to_clean:
                await db.users.delete_one({"email": email})

        asyncio.run(run_cleanup())
        client.close()


@pytest.fixture(scope="function")
def clean_user_now():
    from pymongo import MongoClient

    async def delete_user(email):
        client = MongoClient("mongodb://localhost:27018/?directConnection=true")
        try:
            db = client["8_films"]
            db.users.delete_one({"email": email})
        finally:
            client.close()

    return delete_user


@pytest.fixture(scope="function")
def prepare_db_without_basic_plan():
    basic_plan = None

    async def setup():
        nonlocal basic_plan
        client = AsyncIOMotorClient("mongodb://localhost:27018/?directConnection=true")
        db = client["8_films"]

        basic_plan = await db.subscriptionplans.find_one({"price": 0})
        if basic_plan:
            await db.subscriptionplans.delete_one({"price": 0})
        client.close()

    async def cleanup():
        nonlocal basic_plan
        client = AsyncIOMotorClient("mongodb://localhost:27018/?directConnection=true")
        db = client["8_films"]
        if basic_plan:
            basic_plan.pop("_id", None)
            await db.subscriptionplans.insert_one(basic_plan)
        client.close()
        await asyncio.sleep(1)

    asyncio.run(setup())
    yield
    asyncio.run(cleanup())
