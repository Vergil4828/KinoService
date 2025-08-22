from backend.core.redis_client import get_redis_client, init_redis, close_redis
import pytest


@pytest.mark.asyncio
@pytest.mark.positive
class TestLogoutUserPositive:
    async def test_logout_user_positive(
        self, api_client_user, registered_user_in_db_per_function
    ):
        user_data, response_data = await registered_user_in_db_per_function(None)
        accessToken = response_data.json()["accessToken"]
        user_id = response_data.json()["user"]["id"]
        await api_client_user.get_user_data(accessToken)
        await init_redis()
        redis_client = get_redis_client()
        if redis_client:
            refresh_token_in_redis_before_logout = await redis_client.exists(
                f"refresh_token:{user_id}"
            )
            user_data_in_redis_before_logout = await redis_client.exists(
                f"user_data:{user_id}"
            )
            assert refresh_token_in_redis_before_logout == 1
            assert user_data_in_redis_before_logout == 1

        response = await api_client_user.logout_user(accessToken)
        if redis_client:
            refresh_token_in_redis_after_logout = await redis_client.exists(
                f"refresh_token:{user_id}"
            )
            user_data_in_redis_after_logout = await redis_client.exists(
                f"user_data:{user_id}"
            )
            assert refresh_token_in_redis_after_logout == 0
            assert user_data_in_redis_after_logout == 0
        assert response.status_code == 200
        assert response.json()["message"] == "Logout successful"
        assert (
            refresh_token_in_redis_before_logout != refresh_token_in_redis_after_logout
        )
        assert user_data_in_redis_before_logout != user_data_in_redis_after_logout
        await close_redis()
