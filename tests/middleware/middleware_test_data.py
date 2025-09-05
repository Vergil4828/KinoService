import os
import mimetypes
from tests.data.API_User.user_test_data import UpdateUserData

TEST_UPLOAD_AVATARS_DIR = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "data",
    "API_User",
    "avatars_test_upload_user",
)
image_path = os.path.join(TEST_UPLOAD_AVATARS_DIR, "valid_avatars", "file_positive.jpg")
with open(image_path, "rb") as image_file:
    image_content = image_file.read()
    content_type, _ = mimetypes.guess_type("file_positive.jpg")
files_to_upload = {"avatar": ("file_positive.jpg", image_content, content_type)}


class UserWalletSubscriptionData:
    data = [
        (
            "api_client_user",
            lambda client, token: client.get_user_data(token),
        ),
        (
            "api_client_user",
            lambda client, token: client.update_user(
                token, UpdateUserData.base_user_update_data
            ),
        ),
        ("api_client_user", lambda client, token: client.logout_user(token)),
        (
            "api_client_user",
            lambda client, token: client.upload_avatar(token, files_to_upload),
        ),
        ("api_client_wallet", lambda client, token: client.get_user_wallet(token)),
        ("api_client_wallet", lambda client, token: client.wallet_deposit(token, 500)),
    ]
