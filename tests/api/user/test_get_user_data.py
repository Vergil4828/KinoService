import pytest

from tests.api.user.user_client import UserClient
from tests.conftest import (
    clean_cache_redis,
    UserCreationFunction,
    UserCleanFunction,
)


@pytest.mark.asyncio
@pytest.mark.positive
class TestGetUserDataPositive:

    async def test_get_user_data_valid_access_token(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_function: UserCreationFunction,
    ):
        user_data, response_data, accessToken = (
            await registered_user_in_db_per_function(None)
        )
        response = await api_client_user.get_user_data(accessToken)

        assert response.status_code == 200
        assert response.json()["user"]["username"] == user_data["username"]
        assert response.json()["user"]["email"] == user_data["email"]
        await clean_cache_redis(f"user_data:{response_data.json()['user']['id']}")


@pytest.mark.asyncio
@pytest.mark.negative
class TestGetUserDataNegative:
    async def test_get_user_data_after_user_delete_in_db(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_function: UserCreationFunction,
        clean_user_now: UserCleanFunction,
    ):
        user_data, response_data, accessToken = (
            await registered_user_in_db_per_function(None)
        )
        await clean_user_now(response_data.json()["user"]["id"])
        response = await api_client_user.get_user_data(accessToken)
        assert response.status_code == 401
