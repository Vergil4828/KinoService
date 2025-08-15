from jose import jwt
import pytest, time, asyncio


@pytest.mark.asyncio
@pytest.mark.positive
class TestRefreshTokenPositive:
    async def test_get_tokens_positive(
        self, api_client_user, registered_user_in_db_per_function
    ):
        user_data, response_data = await registered_user_in_db_per_function(
            {
                "username": "new_tokens_user",
                "email": "new_tokens@example.com",
                "password": "Password123",
                "confirmPassword": "Password123",
            }
        )
        accessToken = response_data.json()["accessToken"]
        refreshToken = response_data.json()["refreshToken"]
        await asyncio.sleep(1)
        response = await api_client_user.get_new_tokens(refreshToken)
        assert response.status_code == 200
        assert response.json()["accessToken"] != accessToken
        assert response.json()["refreshToken"] != refreshToken


@pytest.mark.asyncio
@pytest.mark.negative
class TestRefreshTokenNegative:

    async def test_get_tokens_after_user_delete_in_db(
        self, api_client_user, registered_user_in_db_per_function, clean_user_now
    ):
        user_data, response_data = await registered_user_in_db_per_function(None)
        refreshToken = response_data.json()["refreshToken"]
        await clean_user_now(user_data["email"])
        response = await api_client_user.get_new_tokens(refreshToken)
        assert response.status_code == 401
        assert response.json()["detail"] == "User not found"

    async def test_get_tokens_with_expired_refresh_token(
        self, api_client_user, registered_user_in_db_per_class
    ):
        user_data, response_data = await registered_user_in_db_per_class(None)
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

    async def test_get_tokens_with_not_refresh_token(self, api_client_user):
        response = await api_client_user.get_new_tokens("")
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"

    async def test_get_tokens_with_invalid_refresh_token(
        self, api_client_user, registered_user_in_db_per_class
    ):
        user_data, response_data = await registered_user_in_db_per_class(None)
        refreshToken = response_data.json()["refreshToken"] + "XXX"
        response = await api_client_user.get_new_tokens(refreshToken)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"
