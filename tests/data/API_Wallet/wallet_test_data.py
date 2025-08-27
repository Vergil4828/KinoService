import pytest


class WalletDepositData:
    invalid_amount = [
        (9.99, 422),
        (None, 422),
        (True, 422),
        (False, 422),
        ("asdadasdsa", 422),
        ("", 422),
        (10.000001, 422),
        pytest.param("inf", 422),
        pytest.param("nan", 422),
    ]
