import pytest, uuid
from backend.core.redis_client import get_redis_client, init_redis, close_redis
from tests.data.API_User.user_test_data import UpdateUserData


@pytest.mark.asyncio
@pytest.mark.positive
class TestUpdateUserPositive:

    async def test_update_user_positive(
        self, api_client_user, registered_user_in_db_per_function
    ):
        update_user_data = UpdateUserData.base_user_update_data.copy()
        update_user_data["username"] = "update_user"
        update_user_data["email"] = "update_email@example.com"
        update_user_data["newPassword"] = "Password1234"
        _, response_data, accessToken = await registered_user_in_db_per_function(None)
        response = await api_client_user.update_user(accessToken, update_user_data)
        assert response.status_code == 200
        assert response.json()["user"]["username"] == update_user_data["username"]
        assert response.json()["user"]["email"] == update_user_data["email"]

    async def test_update_user_delete_cache_user_data_after_update(
        self, api_client_user, registered_user_in_db_per_function
    ):
        update_user_data = UpdateUserData.base_user_update_data.copy()
        update_user_data["username"] = "update_user"
        update_user_data["email"] = "update_email@example.com"
        update_user_data["newPassword"] = "Password1234"
        _, response_data, accessToken = await registered_user_in_db_per_function(None)

        await api_client_user.get_user_data(accessToken)
        user_id = response_data.json()["user"]["id"]
        await init_redis()
        redis_client = get_redis_client()
        if redis_client:
            user_data_before_update = await redis_client.exists(f"user_data:{user_id}")
            assert user_data_before_update == 1
        response = await api_client_user.update_user(accessToken, update_user_data)
        if redis_client:
            user_data_after_update = await redis_client.exists(f"user_data:{user_id}")
            assert user_data_after_update == 0
        assert response.status_code == 200
        assert response.json()["user"]["username"] == update_user_data["username"]
        assert response.json()["user"]["email"] == update_user_data["email"]
        assert user_data_before_update != user_data_after_update
        await close_redis()


@pytest.mark.asyncio
@pytest.mark.positive
class TestUpdateUserValidValidation:
    @pytest.mark.parametrize(
        "username, status_code, ids",
        UpdateUserData.test_data_valid_username,
        ids=[data[2] for data in UpdateUserData.test_data_valid_username],
    )
    async def test_update_user_valid_username(
        self,
        api_client_user,
        registered_user_in_db_per_class,
        username,
        status_code,
        ids,
    ):
        status_code = 200
        update_user_data = UpdateUserData.base_user_update_data.copy()
        user_data, response_data, accessToken = await registered_user_in_db_per_class(None)
        update_user_data["username"] = username
        update_user_data["email"] = user_data["email"]
        response = await api_client_user.update_user(accessToken, update_user_data)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "email, status_code, ids",
        UpdateUserData.test_data_valid_email,
        ids=[data[2] for data in UpdateUserData.test_data_valid_email],
    )
    async def test_update_user_valid_email(
        self,
        api_client_user,
        registered_user_in_db_per_class,
        email,
        status_code,
        ids,
    ):
        status_code = 200
        update_user_data = UpdateUserData.base_user_update_data.copy()
        _, response_data, accessToken = await registered_user_in_db_per_class(None)
        update_user_data["email"] = email
        response = await api_client_user.update_user(accessToken, update_user_data)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "new_password, status_code, ids",
        UpdateUserData.test_data_valid_new_password,
        ids=[data[2] for data in UpdateUserData.test_data_valid_new_password],
    )
    async def test_update_user_valid_new_password(
        self,
        api_client_user,
        registered_user_in_db_per_function,
        new_password,
        status_code,
        ids,
    ):
        status_code = 200
        update_user_data = UpdateUserData.base_user_update_data.copy()
        user_data, response_data, accessToken = await registered_user_in_db_per_function(None)
        update_user_data["email"] = user_data["email"]
        update_user_data["newPassword"] = new_password
        response = await api_client_user.update_user(accessToken, update_user_data)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "current_password, status_code, ids",
        UpdateUserData.test_data_valid_current_password,
        ids=[data[2] for data in UpdateUserData.test_data_valid_current_password],
    )
    async def test_update_user_valid_current_password(
        self,
        api_client_user,
        registered_user_in_db_per_function,
        current_password,
        status_code,
        ids,
    ):
        status_code = 200
        update_user_data = UpdateUserData.base_user_update_data.copy()
        email = f"{uuid.uuid4()}@example.com"
        _, response_data, accessToken = await registered_user_in_db_per_function(
            {
                "username": "new_user",
                "email": email,
                "password": current_password,
                "confirmPassword": current_password,
            }
        )
        update_user_data["currentPassword"] = current_password
        update_user_data["email"] = email
        response = await api_client_user.update_user(accessToken, update_user_data)
        assert response.status_code == status_code


@pytest.mark.asyncio
@pytest.mark.negative
class TestUpdateUserInvalidValidation:
    @pytest.mark.parametrize(
        "username, status_code, ids",
        UpdateUserData.test_data_invalid_username,
        ids=[data[2] for data in UpdateUserData.test_data_invalid_username],
    )
    async def test_update_user_invalid_username(
        self,
        api_client_user,
        registered_user_in_db_per_class,
        username,
        status_code,
        ids,
    ):
        update_user_data = UpdateUserData.base_user_update_data.copy()
        user_data, response_data, accessToken = await registered_user_in_db_per_class(None)
        update_user_data["username"] = username
        update_user_data["email"] = user_data["email"]
        response = await api_client_user.update_user(accessToken, update_user_data)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "email, status_code, ids",
        UpdateUserData.test_data_invalid_email,
        ids=[data[2] for data in UpdateUserData.test_data_invalid_email],
    )
    async def test_update_user_invalid_email(
        self,
        api_client_user,
        registered_user_in_db_per_class,
        email,
        status_code,
        ids,
    ):
        update_user_data = UpdateUserData.base_user_update_data.copy()
        _, response_data, accessToken = await registered_user_in_db_per_class(None)
        update_user_data["email"] = email
        response = await api_client_user.update_user(accessToken, update_user_data)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "new_password, status_code, ids",
        UpdateUserData.test_data_invalid_new_password,
        ids=[data[2] for data in UpdateUserData.test_data_invalid_new_password],
    )
    async def test_update_user_invalid_new_password(
        self,
        api_client_user,
        registered_user_in_db_per_class,
        new_password,
        status_code,
        ids,
    ):
        update_user_data = UpdateUserData.base_user_update_data.copy()
        user_data, response_data, accessToken = await registered_user_in_db_per_class(None)
        update_user_data["newPassword"] = new_password
        update_user_data["email"] = user_data["email"]
        response = await api_client_user.update_user(accessToken, update_user_data)

        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "current_password, status_code, ids",
        UpdateUserData.test_data_invalid_current_password,
        ids=[data[2] for data in UpdateUserData.test_data_invalid_current_password],
    )
    async def test_update_user_invalid_current_password(
        self,
        api_client_user,
        registered_user_in_db_per_class,
        current_password,
        status_code,
        ids,
    ):
        update_user_data = UpdateUserData.base_user_update_data.copy()
        user_data, response_data, accessToken = await registered_user_in_db_per_class(None)
        update_user_data["currentPassword"] = current_password
        update_user_data["email"] = user_data["email"]
        response = await api_client_user.update_user(accessToken, update_user_data)
        assert response.status_code == status_code


@pytest.mark.asyncio
@pytest.mark.negative
class TestUpdateUserNegative:

    async def test_update_user_after_user_delete_in_db(
        self, api_client_user, registered_user_in_db_per_function, clean_user_now
    ):
        user_data, response_data, accessToken = await registered_user_in_db_per_function(None)
        update_user_data = UpdateUserData.base_user_update_data.copy()
        update_user_data["email"] = user_data["email"]
        await clean_user_now(response_data.json()["user"]["id"])
        response = await api_client_user.update_user(accessToken, update_user_data)
        assert response.status_code == 401
        assert response.json()["detail"] == "User not found"

    async def test_update_user_with_wrong_password(
        self, api_client_user, registered_user_in_db_per_function
    ):
        user_data, response_data, accessToken = await registered_user_in_db_per_function(None)
        update_user_data = UpdateUserData.base_user_update_data.copy()
        update_user_data["currentPassword"] = "Password1234"
        update_user_data["email"] = user_data["email"]
        response = await api_client_user.update_user(accessToken, update_user_data)
        assert response.status_code == 400

    async def test_update_user_missing_required_field(
        self, api_client_user, registered_user_in_db_per_function
    ):
        user_data, response_data, accessToken = await registered_user_in_db_per_function(None)
        update_user_data = UpdateUserData.base_user_update_data.copy()
        update_user_data["email"] = user_data["email"]
        del update_user_data["currentPassword"]
        response = await api_client_user.update_user(accessToken, update_user_data)
        assert response.status_code == 422
        assert response.json()["detail"][0]["msg"] == "Field required"

    async def test_login_user_with_duplicate_field(
        self, api_client_user, clean_user_now, registered_user_in_db_per_function
    ):
        user_data, response_data, accessToken = await registered_user_in_db_per_function(None)
        update_user_data = {
            "username": "new_user",
            "email": "user@example.com",
            "newPassword": "Password123",
            "currentPassword": "Password123",
            "username": "dupli_user",
            "email": "dupli_user@example.com",
            "newPassword": "Password1234",
            "currentPassword": "Password123",
        }
        response = await api_client_user.update_user(accessToken, update_user_data)
        assert response.status_code == 200
        assert response.json()["user"]["username"] == "dupli_user"
        assert response.json()["user"]["email"] == "dupli_user@example.com"
        await clean_user_now(response.json()["user"]["_id"])
