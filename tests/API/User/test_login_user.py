import pytest
import uuid

from tests.API.User.user_client import UserClient
from tests.conftest import UserCreationFunction
from tests.data.API_User.user_test_data import LoginUserData


@pytest.mark.asyncio
@pytest.mark.positive
class TestLoginUserPositive:
    @pytest.mark.parametrize(
        "email, password, status_code, ids",
        LoginUserData.positive_test_data,
        ids=[data[3] for data in LoginUserData.positive_test_data],
    )
    async def test_login_user(
        self,
        api_client_user: UserClient,
        email: str,
        password: str,
        status_code: int,
        ids: str,
        registered_user_in_db_per_function: UserCreationFunction,
    ):
        await registered_user_in_db_per_function(
            {
                "username": "user_now",
                "email": email,
                "password": password,
                "confirmPassword": password,
            }
        )
        credential = {"email": email, "password": password}
        response = await api_client_user.login_user(credential)
        assert response.status_code == status_code
        assert "accessToken" in response.json()
        assert "refreshToken" in response.json()


@pytest.mark.asyncio
@pytest.mark.positive
class TestLoginUserValidValidation:

    @pytest.mark.parametrize(
        "email, status_code, ids",
        LoginUserData.test_data_valid_email,
        ids=[data[2] for data in LoginUserData.test_data_valid_email],
    )
    async def test_login_user_valid_email(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_function: UserCreationFunction,
        email: str,
        status_code: int,
        ids: str,
    ):
        status_code = 200
        await registered_user_in_db_per_function(
            {
                "username": "user_now",
                "email": email,
                "password": "Password123",
                "confirmPassword": "Password123",
            }
        )
        credential = {"email": email, "password": "Password123"}
        response = await api_client_user.login_user(credential)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "password, status_code, ids",
        LoginUserData.test_data_valid_password,
        ids=[data[2] for data in LoginUserData.test_data_valid_password],
    )
    async def test_login_user_valid_password(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_function: UserCreationFunction,
        password: str,
        status_code: int,
        ids: str,
    ):
        email = f"user-{uuid.uuid4()}@example.com"
        await registered_user_in_db_per_function(
            {
                "username": "user_now",
                "email": email,
                "password": password,
                "confirmPassword": password,
            }
        )
        credential = {"email": email, "password": password}
        response = await api_client_user.login_user(credential)
        assert response.status_code == status_code


@pytest.mark.asyncio
@pytest.mark.negative
class TestLoginUserInvalidValidation:

    @pytest.mark.parametrize(
        "email, status_code, ids",
        LoginUserData.test_data_invalid_email,
        ids=[data[2] for data in LoginUserData.test_data_invalid_email],
    )
    async def test_login_user_invalid_email(
        self, api_client_user: UserClient, email: str, status_code: int, ids: str
    ):
        credential = LoginUserData.base_credential.copy()
        credential["email"] = email
        response = await api_client_user.login_user(credential)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "password, status_code, ids",
        LoginUserData.test_data_invalid_password,
        ids=[data[2] for data in LoginUserData.test_data_invalid_password],
    )
    async def test_login_user_invalid_password(
        self, api_client_user: UserClient, password: str, status_code: int, ids: str
    ):
        credential = LoginUserData.base_credential.copy()
        credential["email"] = f"user-{uuid.uuid4()}@example.com"
        credential["password"] = password
        response = await api_client_user.login_user(credential)
        assert response.status_code == status_code


@pytest.mark.asyncio
@pytest.mark.negative
class TestLoginUserNegative:

    async def test_login_user_with_not_exists_email_in_database(
        self, api_client_user: UserClient
    ):
        response = await api_client_user.login_user(
            LoginUserData.base_credential.copy()
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    async def test_login_user_with_wrong_password_for_email_in_db(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_function: UserCreationFunction,
    ):
        credential = LoginUserData.base_credential.copy()
        await registered_user_in_db_per_function(
            {
                "username": "user_now",
                "email": credential["email"],
                "password": credential["password"],
                "confirmPassword": credential["password"],
            }
        )

        credential["password"] = credential["password"] + "123"
        response = await api_client_user.login_user(credential)
        assert response.status_code == 401

    @pytest.mark.parametrize(
        "field_to_remove, status_code", [("email", 422), ("password", 422)]
    )
    async def test_login_user_missing_required_field(
        self, api_client_user: UserClient, field_to_remove: str, status_code: int
    ):
        credential = LoginUserData.base_credential.copy()
        del credential[field_to_remove]
        response = await api_client_user.login_user(credential)
        assert response.status_code == status_code
        assert response.json()["detail"][0]["msg"] == "Field required"

    async def test_login_user_with_duplicate_field(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_function: UserCreationFunction,
    ):
        await registered_user_in_db_per_function(
            {
                "username": "dupli_user",
                "email": "dupli@example.com",
                "password": "Password1234",
                "confirmPassword": "Password1234",
            }
        )
        credential = {
            "email": "user@example.com",
            "email": "dupli@example.com",
            "password": "Password123",
            "password": "Password1234",
        }
        response = await api_client_user.login_user(credential)

        assert response.status_code == 200
        assert response.json()["user"]["username"] == "dupli_user"
        assert response.json()["user"]["email"] == "dupli@example.com"
