from jose import jwt
import pytest, time
from .middleware_test_data import UserWalletSubscriptionData


@pytest.mark.parametrize(
    "route_client_name, client_func", UserWalletSubscriptionData.data
)
@pytest.mark.asyncio
@pytest.mark.negative
class TestMiddlewareNegative:
    async def test_request_without_header_authorization(
        self, route_client_name, client_func, api_client_user
    ):
        response = await client_func(api_client_user, "")
        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication required"

    async def test_request_wrong_header_authorization(
        self,
        route_client_name,
        client_func,
        api_client_user,
        registered_user_in_db_per_class,
    ):
        user_data, response_data = await registered_user_in_db_per_class(None)
        accessToken = response_data.json().copy()["accessToken"]
        wrong_format_header_authorization = "token " + accessToken
        response = await client_func(api_client_user, wrong_format_header_authorization)
        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication required"

    async def test_expired_access_token(
        self,
        route_client_name,
        client_func,
        api_client_user,
        registered_user_in_db_per_class,
    ):
        user_data, response_data = await registered_user_in_db_per_class(None)
        valid_token = response_data.json().copy()["accessToken"]
        valid_payload = jwt.decode(
            valid_token,
            key="fake_key",
            algorithms=["HS256"],
            options={"verify_signature": False},
        )
        user_id = valid_payload.get("userId")
        from backend.core.config import JWT_SECRET_KEY, JWT_ALGORITHM

        expired_payload = {
            "userId": user_id,
            "exp": int(time.time()) - 60,
        }
        expired_token = jwt.encode(
            expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
        )
        response = await client_func(api_client_user, expired_token)
        assert response.status_code == 401
        assert response.json()["detail"] == "Token expired"

    async def test_request_after_modify_token(
        self,
        route_client_name,
        client_func,
        api_client_user,
        registered_user_in_db_per_class,
    ):
        user_data, response_data = await registered_user_in_db_per_class(None)
        accessToken = response_data.json().copy()["accessToken"] + "XXX"
        response = await client_func(api_client_user, accessToken)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"
