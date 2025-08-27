import pytest

from tests.API.conftest import clean_cache_redis


@pytest.mark.asyncio
@pytest.mark.positive
class TestGetUserWalletPositive:
    async def test_get_user_wallet_valid_access_token(
        self, api_client_wallet, registered_user_in_db_per_function
    ):
        user_data, response_data, accessToken = (
            await registered_user_in_db_per_function(None)
        )
        response = await api_client_wallet.get_user_wallet(accessToken)

        assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.negative
class TestGetUserWalletNegative:
    async def test_get_user_wallet_after_user_delete_in_db(
        self, api_client_wallet, registered_user_in_db_per_function, clean_user_now
    ):
        user_data, response_data, accessToken = (
            await registered_user_in_db_per_function(None)
        )
        await clean_user_now(response_data.json()["user"]["id"])
        response = await api_client_wallet.get_user_wallet(accessToken)
        assert response.status_code == 401
