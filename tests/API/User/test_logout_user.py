import pytest


@pytest.mark.asyncio
@pytest.mark.positive
class TestLogoutUserPositive:
    async def test_logout_user_positive(
        self, api_client_user, registered_user_in_db_per_function
    ):
        user_data, response_data = await registered_user_in_db_per_function(None)
        accessToken = response_data.json()["accessToken"]
        response = await api_client_user.logout_user(accessToken)
        assert response.status_code == 200
        assert response.json()["message"] == "Logout successful"
