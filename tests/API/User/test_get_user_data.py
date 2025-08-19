from jose import jwt
import pytest, time


@pytest.mark.asyncio
@pytest.mark.positive
class TestGetUserDataPositive:

    async def test_get_user_data_valid_access_token(
        self, api_client_user, registered_user_in_db_per_function
    ):
        user_data, response_data = await registered_user_in_db_per_function(None)
        accessToken = response_data.json()["accessToken"]
        response = await api_client_user.get_user_data(accessToken)
        assert response.status_code == 200
        assert response.json()["user"]["username"] == user_data["username"]
        assert response.json()["user"]["email"] == user_data["email"]


@pytest.mark.asyncio
@pytest.mark.negative
class TestGetUserDataNegative:
    async def test_get_user_data_after_user_delete_in_db(
        self, api_client_user, registered_user_in_db_per_function, clean_user_now
    ):
        user_data, response_data = await registered_user_in_db_per_function(None)
        accessToken = response_data.json()["accessToken"]
        await clean_user_now(response_data.json()["user"]["id"])
        response = await api_client_user.get_user_data(accessToken)
        assert response.status_code == 401
