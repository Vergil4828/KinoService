from tests.API.User.user_test_data import UpdateUserData


class UserWalletSubscriptionData:
    data = [
        (
            "get_user_data",
            lambda client, token: client.get_user_data(token),
        ),
        (
            "update_user",
            lambda client, token: client.update_user(
                token, UpdateUserData.base_user_update_data
            ),
        ),
        ("logout_user", lambda client, token: client.logout_user(token)),
        (
            "upload_avatar",
            lambda client, token: client.upload_avatar(
                token, ("test.jpg", b"fake_image_data", "image/jpeg")
            ),
        ),
    ]
