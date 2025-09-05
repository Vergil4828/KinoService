import pytest
import os
import aiofiles
import mimetypes
from backend.core.redis_client import get_redis_client, init_redis, close_redis
from tests.API.User.user_client import UserClient
from tests.conftest import UserCreationFunction, UserCleanFunction

TEST_UPLOAD_AVATARS_DIR = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
    "data",
    "API_User",
    "avatars_test_upload_user",
)


@pytest.mark.asyncio
@pytest.mark.positive
class TestUploadAvatarPositive:
    @pytest.mark.parametrize("file_extension", ["jpeg", "jpg", "gif", "png"])
    async def test_upload_valid_avatar(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_class: UserCreationFunction,
        file_extension: str,
    ):
        user_data, response_data, accessToken = await registered_user_in_db_per_class(
            None
        )
        filename = f"file_positive.{file_extension}"
        image_path = os.path.join(TEST_UPLOAD_AVATARS_DIR, "valid_avatars", filename)
        async with aiofiles.open(image_path, "rb") as image_file:
            image_content = await image_file.read()
            content_type, _ = mimetypes.guess_type(filename)
            files_to_upload = {"avatar": (filename, image_content, content_type)}
            response = await api_client_user.upload_avatar(
                files=files_to_upload, token=accessToken
            )
        assert response.status_code == 200
        assert (
            response.json()["user"]["avatar"] != response_data.json()["user"]["avatar"]
        )

    async def test_upload_avatar_max_file_size(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_class: UserCreationFunction,
    ):
        user_data, response_data, accessToken = await registered_user_in_db_per_class(
            None
        )
        filename = "file_positive_2_mb.jpg"
        image_path = os.path.join(TEST_UPLOAD_AVATARS_DIR, "valid_avatars", filename)
        async with aiofiles.open(image_path, "rb") as image_file:
            image_content = await image_file.read()
            content_type, _ = mimetypes.guess_type(filename)
            files_to_upload = {"avatar": (filename, image_content, content_type)}
            response = await api_client_user.upload_avatar(
                files=files_to_upload, token=accessToken
            )
        assert response.status_code == 200

    async def test_cache_user_data_delete_after_upload_avatar(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_class: UserCreationFunction,
    ):
        user_data_before_upload = user_data_after_upload = None
        user_data, response_data, accessToken = await registered_user_in_db_per_class(
            None
        )
        await api_client_user.get_user_data(accessToken)
        user_id = response_data.json()["user"]["id"]
        await init_redis()
        redis_client = get_redis_client()
        if redis_client:
            user_data_before_upload = await redis_client.exists(f"user_data:{user_id}")
            assert user_data_before_upload == 1

        filename = "file_positive_2_mb.jpg"
        image_path = os.path.join(TEST_UPLOAD_AVATARS_DIR, "valid_avatars", filename)
        async with aiofiles.open(image_path, "rb") as image_file:
            image_content = await image_file.read()
            content_type, _ = mimetypes.guess_type(filename)
            files_to_upload = {"avatar": (filename, image_content, content_type)}
            response = await api_client_user.upload_avatar(
                files=files_to_upload, token=accessToken
            )
        if redis_client:
            user_data_after_upload = await redis_client.exists(f"user_data:{user_id}")
            assert user_data_after_upload == 0
        assert user_data_before_upload != user_data_after_upload
        assert response.status_code == 200
        await close_redis()


@pytest.mark.asyncio
@pytest.mark.negative
class TestUploadAvatarNegative:

    async def test_upload_avatar_after_delete_user_in_db(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_function: UserCreationFunction,
        clean_user_now: UserCleanFunction,
    ):
        user_data, response_data, accessToken = (
            await registered_user_in_db_per_function(None)
        )
        await clean_user_now(response_data.json()["user"]["id"])
        filename = "file_positive_2_mb.jpg"
        image_path = os.path.join(TEST_UPLOAD_AVATARS_DIR, "valid_avatars", filename)
        async with aiofiles.open(image_path, "rb") as image_file:
            image_content = await image_file.read()
            content_type, _ = mimetypes.guess_type(filename)
            files_to_upload = {"avatar": (filename, image_content, content_type)}
            response = await api_client_user.upload_avatar(
                files=files_to_upload, token=accessToken
            )
        assert response.status_code == 401
        assert response.json()["detail"] == "User not found"

    @pytest.mark.parametrize(
        "file_extension",
        [
            "7z",
            "bin",
            "docx",
            "exe",
            "html",
            "iso",
            "mp3",
            "mp4",
            "msi",
            "pdf",
            "pptx",
            "svg",
            "txt",
            "wav",
            "xlsx",
            "zip",
        ],
    )
    async def test_upload_invalid_avatar_extension(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_class: UserCreationFunction,
        file_extension: str,
    ):
        user_data, response_data, accessToken = await registered_user_in_db_per_class(
            None
        )
        filename = f"file_invalid_extension.{file_extension}"
        image_path = os.path.join(TEST_UPLOAD_AVATARS_DIR, "invalid_avatars", filename)
        async with aiofiles.open(image_path, "rb") as image_file:
            image_content = await image_file.read()
            content_type, _ = mimetypes.guess_type(filename)
            files_to_upload = {"avatar": (filename, image_content, content_type)}
            response = await api_client_user.upload_avatar(
                files=files_to_upload, token=accessToken
            )
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Разрешены только файлы изображений (JPEG, PNG, GIF)."
        )

    async def test_upload_avatar_invalid_content_type(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_class: UserCreationFunction,
    ):
        user_data, response_data, accessToken = await registered_user_in_db_per_class(
            None
        )
        filename = "file_invalid_extension.exe"
        image_path = os.path.join(TEST_UPLOAD_AVATARS_DIR, "invalid_avatars", filename)
        async with aiofiles.open(image_path, "rb") as image_file:
            image_content = await image_file.read()
            invalid_content_type = "image/jpeg"
            files_to_upload = {
                "avatar": (filename, image_content, invalid_content_type)
            }
            response = await api_client_user.upload_avatar(
                files=files_to_upload, token=accessToken
            )
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Разрешены только файлы изображений (JPEG, PNG, GIF)."
        )

    async def test_upload_avatar_more_2_mb(
        self,
        api_client_user: UserClient,
        registered_user_in_db_per_class: UserCreationFunction,
    ):
        user_data, response_data, accessToken = await registered_user_in_db_per_class(
            None
        )
        filename = "file_invalid_more_2_mb.jpg"
        image_path = os.path.join(TEST_UPLOAD_AVATARS_DIR, "invalid_avatars", filename)
        async with aiofiles.open(image_path, "rb") as image_file:
            image_content = await image_file.read()
            content_type, _ = mimetypes.guess_type(filename)
            files_to_upload = {"avatar": (filename, image_content, content_type)}
            response = await api_client_user.upload_avatar(
                files=files_to_upload, token=accessToken
            )
        assert response.status_code == 400
        assert response.json()["detail"] == "Размер файла превышает 2MB."
