from jose import jwt
from backend.core.redis_client import get_redis_client, init_redis, close_redis
import pytest
import time
import asyncio

from tests.API.User.user_client import UserClient
from tests.conftest import UserCreationFunction, UserCleanFunction


@pytest.mark.asyncio
@pytest.mark.positive
class TestRefreshTokenPositive:
    async def test_get_tokens_positive(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_function: UserCreationFunction,
    ):
        user_data, response_data, accessToken = (
            await registered_user_in_db_per_function(
                {
                    "username": "new_tokens_user",
                    "email": "new_tokens@example.com",
                    "password": "Password123",
                    "confirmPassword": "Password123",
                }
            )
        )
        refreshToken = response_data.json()["refreshToken"]
        await asyncio.sleep(1)
        response = await api_client_user.get_new_tokens(refreshToken)
        assert response.status_code == 200
        assert response.json()["accessToken"] != accessToken
        assert response.json()["refreshToken"] != refreshToken


@pytest.mark.asyncio
@pytest.mark.negative
class TestRefreshTokenNegative:

    async def test_get_tokens_after_user_token_delete_in_redis(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_function: UserCreationFunction,
    ):
        user_data, response_data, _ = await registered_user_in_db_per_function(None)
        refreshToken = response_data.json()["refreshToken"]
        user_id = response_data.json()["user"]["id"]
        await init_redis()
        redis_client = get_redis_client()
        if redis_client:
            await redis_client.delete(f"refresh_token:{user_id}")
        await close_redis()
        response = await api_client_user.get_new_tokens(refreshToken)
        assert response.status_code == 401
        assert response.json()["detail"] == "User token not in the Redis"

    async def test_get_tokens_after_user_delete_in_db(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_function: UserCreationFunction,
        clean_user_now: UserCleanFunction,
    ):
        user_data, response_data, _ = await registered_user_in_db_per_function(None)
        refreshToken = response_data.json()["refreshToken"]
        await clean_user_now(response_data.json()["user"]["id"])
        response = await api_client_user.get_new_tokens(refreshToken)
        assert response.status_code == 401
        assert response.json()["detail"] == "User token not in the Redis"

    async def test_get_tokens_with_expired_refresh_token(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_class: UserCreationFunction,
    ):
        user_data, response_data, _ = await registered_user_in_db_per_class(None)
        valid_token = response_data.json().copy()["refreshToken"]
        valid_payload = jwt.decode(
            valid_token,
            key="fake_key",
            algorithms=["HS256"],
            options={"verify_signature": False},
        )
        user_id = valid_payload.get("userId")
        from backend.core.config import REFRESH_SECRET_KEY, JWT_ALGORITHM

        expired_payload = {
            "userId": user_id,
            "exp": int(time.time()) - 60,
        }
        expired_token = jwt.encode(
            expired_payload, REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM
        )
        response = await api_client_user.get_new_tokens(expired_token)
        assert response.status_code == 401
        assert response.json()["detail"] == "Token expired"

    async def test_get_tokens_with_not_refresh_token(self, api_client_user: UserClient):
        response = await api_client_user.get_new_tokens("")
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"

    async def test_get_tokens_with_invalid_refresh_token(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_class: UserCreationFunction,
    ):
        user_data, response_data, _ = await registered_user_in_db_per_class(None)
        refreshToken = response_data.json()["refreshToken"] + "XXX"
        response = await api_client_user.get_new_tokens(refreshToken)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"
