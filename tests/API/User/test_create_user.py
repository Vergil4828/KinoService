import datetime
import time

import pytest, uuid, copy, pytest_asyncio, asyncio
from tests.data.API_User.user_test_data import CreateUserData


@pytest.mark.asyncio
@pytest.mark.positive
class TestCreateUserPositive:

    @pytest.mark.parametrize(
        "username, email, password, confirmPassword, notification_bool, ids",
        CreateUserData.positive_test_data,
        ids=[data[5] for data in CreateUserData.positive_test_data],
    )
    async def test_create_user(
        self,
        api_client_user,
        clean_user_now,
        username,
        email,
        password,
        confirmPassword,
        notification_bool,
        ids,
    ):
        user_data = {
            "username": username,
            "email": email,
            "password": password,
            "confirmPassword": confirmPassword,
            "notifications": {
                "email": notification_bool,
                "push": notification_bool,
                "newsletter": notification_bool,
            },
        }
        response = await api_client_user.register_user(user_data)
        assert response.status_code == 201
        assert response.json()["user"]["email"] == email
        assert "accessToken" in response.json()
        assert "refreshToken" in response.json()
        await clean_user_now(response.json()["user"]["id"])


@pytest.mark.asyncio
@pytest.mark.positive
class TestCreateUserValidValidation:

    @pytest.mark.parametrize(
        "username, status_code, ids",
        CreateUserData.test_data_valid_username,
        ids=[data[2] for data in CreateUserData.test_data_valid_username],
    )
    async def test_create_user_valid_username(
        self, api_client_user, username, status_code, ids, clean_user_now
    ):
        user_data = CreateUserData.base_user_data.copy()
        user_data["email"] = f"user-{uuid.uuid4()}@example.com"
        user_data["username"] = username
        response = await api_client_user.register_user(user_data)
        assert response.status_code == status_code
        await clean_user_now(response.json()["user"]["id"])

    @pytest.mark.parametrize(
        "email, status_code, ids",
        CreateUserData.test_data_valid_email,
        ids=[data[2] for data in CreateUserData.test_data_valid_email],
    )
    async def test_create_user_valid_email(
        self, api_client_user, email, status_code, ids, clean_user_now
    ):
        user_data = CreateUserData.base_user_data.copy()
        user_data["email"] = email
        response = await api_client_user.register_user(user_data)
        assert response.status_code == status_code
        await clean_user_now(response.json()["user"]["id"])

    @pytest.mark.parametrize(
        "password, status_code, ids",
        CreateUserData.test_data_valid_password,
        ids=[data[2] for data in CreateUserData.test_data_valid_password],
    )
    async def test_create_user_valid_passwords(
        self, api_client_user, password, status_code, ids, clean_user_now
    ):
        user_data = CreateUserData.base_user_data.copy()
        user_data["email"] = f"user-{uuid.uuid4()}@example.com"
        user_data["password"] = password
        user_data["confirmPassword"] = password

        response = await api_client_user.register_user(user_data)
        assert response.status_code == status_code
        await clean_user_now(response.json()["user"]["id"])


@pytest.mark.asyncio
@pytest.mark.negative
class TestCreateUserInvalidValidation:

    @pytest.mark.parametrize(
        "username, status_code, ids",
        CreateUserData.test_data_invalid_username,
        ids=[data[2] for data in CreateUserData.test_data_invalid_username],
    )
    async def test_create_user_invalid_username(
        self, api_client_user, username, status_code, ids
    ):
        user_data = CreateUserData.base_user_data.copy()
        user_data["email"] = f"user-{uuid.uuid4()}@example.com"
        user_data["username"] = username
        response = await api_client_user.register_user(user_data)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "email, status_code, ids",
        CreateUserData.test_data_invalid_email,
        ids=[data[2] for data in CreateUserData.test_data_invalid_email],
    )
    async def test_create_user_invalid_email(
        self, api_client_user, email, status_code, ids
    ):
        user_data = CreateUserData.base_user_data.copy()
        user_data["email"] = email
        response = await api_client_user.register_user(user_data)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "password, confirmPassword, status_code, ids",
        CreateUserData.test_data_invalid_password,
        ids=[data[3] for data in CreateUserData.test_data_invalid_password],
    )
    async def test_create_user_invalid_passwords(
        self,
        api_client_user,
        password,
        confirmPassword,
        status_code,
        ids,
    ):
        user_data = CreateUserData.base_user_data.copy()
        user_data["email"] = f"user-{uuid.uuid4()}@example.com"
        user_data["password"] = password
        user_data["confirmPassword"] = confirmPassword

        response = await api_client_user.register_user(user_data)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "field_notifications, value, status_code, ids",
        CreateUserData.test_data_invalid_notifications,
    )
    async def test_create_user_invalid_notifications_fields(
        self, api_client_user, field_notifications, value, status_code, ids
    ):  # Используем глубокое копирование, так как изменяются вложенные данные
        user_data = copy.deepcopy(CreateUserData.base_user_data)
        user_data["email"] = f"user-{uuid.uuid4()}@example.com"
        user_data["notifications"][field_notifications] = value
        response = await api_client_user.register_user(user_data)
        assert response.status_code == status_code


@pytest.mark.asyncio
@pytest.mark.negative
class TestCreateUserNegative:

    async def test_create_user_without_basic_plan(
        self,
        api_client_user,
        prepare_db_and_redis_without_basic_plan,
    ):
        user_data = CreateUserData.base_user_data.copy()
        user_data["email"] = f"user-{uuid.uuid4()}@example.com"
        response = await api_client_user.register_user(user_data)
        assert response.status_code == 500
        assert response.json()["detail"] == "Ошибка сервера при создании пользователя"

    async def test_create_user_with_exist_email_in_database(
        self, api_client_user, registered_user_in_db_per_function
    ):

        user_data, _, _ = await registered_user_in_db_per_function(None)
        response_register = await api_client_user.register_user(user_data)
        assert response_register.status_code == 409
        assert response_register.json()["detail"] == "Email уже занят"

    @pytest.mark.parametrize(
        "field_to_remove, status_code",
        [
            ("username", 422),
            ("email", 422),
            ("password", 422),
            ("confirmPassword", 422),
            ("notifications", 201),
        ],
    )
    async def test_create_user_missing_required_field(
        self, api_client_user, field_to_remove, status_code, clean_user_now
    ):
        user_data_without_field = CreateUserData.base_user_data.copy()
        user_data_without_field["email"] = f"user-{uuid.uuid4()}@example.com"
        del user_data_without_field[field_to_remove]
        response = await api_client_user.register_user(user_data_without_field)
        assert response.status_code == status_code
        if response.status_code == 201:
            await clean_user_now(response.json()["user"]["id"])

    async def test_create_user_with_duplicate_field(
        self, api_client_user, clean_user_now
    ):
        user_data = {
            "username": "new_user",
            "username": "dupli_user",
            "email": "user@example.com",
            "email": "dupli@example.com",
            "password": "Password123",
            "password": "Password1234",
            "confirmPassword": "Password1234",
            "notifications": {"email": False, "push": False, "newsletter": False},
        }

        response = await api_client_user.register_user(user_data)
        assert response.status_code == 201
        assert response.json()["user"]["username"] == "dupli_user"
        assert response.json()["user"]["email"] == "dupli@example.com"
        await clean_user_now(response.json()["user"]["id"])
