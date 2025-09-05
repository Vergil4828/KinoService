import pytest
import asyncio

from tests.api.wallet.wallet_client import WalletClient
from tests.conftest import UserCreationFunction, UserCleanFunction
from tests.data.API_Wallet.wallet_test_data import WalletDepositData


@pytest.mark.asyncio
@pytest.mark.positive
class TestWalletDepositPositive:
    async def test_wallet_deposit_positive(
        self,
        api_client_wallet: WalletClient,
        registered_user_in_db_per_function: UserCreationFunction,
    ):
        _, response_data, accessToken = await registered_user_in_db_per_function(None)
        response = await api_client_wallet.wallet_deposit(accessToken, 10.00)
        assert response.status_code == 200
        response_wallet = await api_client_wallet.get_user_wallet(accessToken)
        assert response_wallet.json()["balance"] == 10.00

    async def test_wallet_deposit_race_condition(
        self,
        api_client_wallet: WalletClient,
        registered_user_in_db_per_function: UserCreationFunction,
    ):
        _, response_data, accessToken = await registered_user_in_db_per_function(None)
        balance_user = response_data.json()["user"]["wallet"]["balance"]
        deposit_amounts = [15, 30, 500, 999.02, 55]
        expected_balance = balance_user + sum(deposit_amounts)
        tasks = [
            api_client_wallet.wallet_deposit(accessToken, amount)
            for amount in deposit_amounts
        ]
        responses = await asyncio.gather(*tasks)
        for response in responses:
            assert response.status_code == 200
        real_balance_user = await api_client_wallet.get_user_wallet(accessToken)
        assert expected_balance == real_balance_user.json()["balance"]


@pytest.mark.asyncio
@pytest.mark.negative
class TestWalletDepositInvalidValidation:

    @pytest.mark.parametrize("amount, status_code", WalletDepositData.invalid_amount)
    async def test_wallet_deposit_invalid_amount(
        self,
        api_client_wallet: WalletClient,
        registered_user_in_db_per_class: UserCreationFunction,
        amount: float,
        status_code: int,
    ):
        _, response_data, accessToken = await registered_user_in_db_per_class(None)
        response = await api_client_wallet.wallet_deposit(accessToken, amount)
        assert response.status_code == status_code


@pytest.mark.asyncio
@pytest.mark.negative
class TestWalletDepositNegative:
    async def test_wallet_deposit_after_user_delete_in_db(
        self,
        api_client_wallet: WalletClient,
        clean_user_now: UserCleanFunction,
        registered_user_in_db_per_function: UserCreationFunction,
    ):
        user_data, response_data, accessToken = (
            await registered_user_in_db_per_function(None)
        )
        await clean_user_now(response_data.json()["user"]["id"])
        response = await api_client_wallet.wallet_deposit(accessToken, 100)
        assert response.status_code == 401
