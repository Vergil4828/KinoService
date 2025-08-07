import pytest


positive_test_data = [
    ("new_user", "user@example.com", "Password123", "Password123", False),
    ("n", "user@example.com", "Password", "Password", True),
]

positive_test_ids = ["Standard user_data", "Minimum password and username length"]


@pytest.mark.positive
class TestCreateUserPositive:
    @pytest.mark.parametrize(
        "username, email, password, confirmPassword, notification_bool",
        positive_test_data,
        ids=positive_test_ids,
    )
    @pytest.mark.asyncio
    async def test_create_user(
        self,
        api_client,
        clean_all_users,
        username,
        email,
        password,
        confirmPassword,
        notification_bool,
    ):
        user_data = {
            "username": username,
            "email": email,
            "password": password,
            "confirmPassword": confirmPassword,
            "notifications": {
                "email": notification_bool,
                "push": notification_bool,
                "newsletter": notification_bool,
            },
        }
        response = await api_client.register_user(user_data)
        assert response.status_code == 201
        assert response.json()["user"]["email"] == email
        assert "accessToken" in response.json()
        assert "refreshToken" in response.json()
        await clean_all_users(email)


user_data_for_negative_test = {
    "username": "new_user",
    "email": "user@example.com",
    "password": "Password123",
    "confirmPassword": "Password123",
    "notifications": {
        "email": False,
        "push": False,
        "newsletter": False,
    },
}

test_data_invalid_username = []

test_data_invalid_email = [
    ("user@example", 422),
    ("userexample.com", 422),
    ("user@", 422),
    ("@example.com", 422),
    (1234567, 422),
    (True, 422),
    (False, 422),
]

test_data_invalid_password = [
    ("Password123", "Password1234", 422, "Password do not match"),
    ("Passwor", "Passwor", 422, "Password length < 8"),
    ("   Password123", "          Password123      ", 201, "Spaces in the password"),
    (12345678, 12345678, 422, "Only numbers in the passwords"),
    (True, True, 422, "Bool [T,T] in the passwords"),
    (False, False, 422, "Bool [F,F] in the passwords"),
    (True, False, 422, "Bool [T,F] in the passwords"),
    (False, True, 422, "Bool [F,T] in the passwords"),
    (None, None, 422, "None in the passwords"),
]


@pytest.mark.negative
class TestCreateUserNegative:
    @pytest.mark.asyncio
    async def test_create_user_without_basic_plan(
        self,
        api_client,
        clean_all_users,
        prepare_db_without_basic_plan,
    ):
        user_data = user_data_for_negative_test.copy()
        response = await api_client.register_user(user_data)
        assert response.status_code == 500
        assert response.json()["detail"] == "Ошибка сервера при создании пользователя"
        await clean_all_users(user_data["email"])

    @pytest.mark.asyncio
    async def test_create_user_with_exist_email_in_database(
        self, api_client, registered_user_in_db, clean_all_users
    ):
        user_data, response = registered_user_in_db
        assert response.status_code == 201

        response_register = await api_client.register_user(user_data)
        assert response_register.status_code == 409
        assert response_register.json()["detail"] == "Email уже занят"
        await clean_all_users(user_data["email"])

    @pytest.mark.parametrize(
        "field_to_remove, status_code",
        [
            ("username", 422),
            ("email", 422),
            ("password", 422),
            ("confirmPassword", 422),
            ("notifications", 201),
        ],
    )
    @pytest.mark.asyncio
    async def test_create_user_missing_required_field(
        self, api_client, field_to_remove, status_code, clean_all_users
    ):
        user_data_without_field = user_data_for_negative_test.copy()
        del user_data_without_field[field_to_remove]
        response = await api_client.register_user(user_data_without_field)
        assert response.status_code == status_code
        if response.status_code == 201:
            await clean_all_users(user_data_without_field["email"])

    # добавить инвалид юзернейм, объеденить то, что можно в один тест
    # ТАКЖЕ НАДО ДОБАВИТЬ ПРОВЕРКИ НА НЕПРАВИЛЬНЫЙ ТИП (С БУЛЛ ЭТО ПРОШЛО, БЫЛА ПУСТАЯ СТРОКА, А С ПАРОЛЕМ - СЕРВЕР УПАЛ)
    # ИЕРОГЛИФЫ В УДАЧНОЙ РЕГЕ И Т.Д.!
    # В ТЕСТ ИТ ДОБАВИТЬ, НЕДОСТАЮЩИЕ ДЛЯ НОТИФИКАЦИИ ( ПУСТЫЕ ЗНАЧЕНИЕ)
    # добавить тест кейс, где будет неправильные значение для полей, в том числе нотификация
    # исправить, удалить предусловия там, где они не нужны
    # оформить потом test_data
    @pytest.mark.parametrize(
        "empty_field", ["username", "email", "password", "confirmPassword"]
    )
    @pytest.mark.asyncio
    async def test_create_user_with_empty_field(self, api_client, empty_field):
        user_data = user_data_for_negative_test.copy()
        user_data[empty_field] = ""
        response = await api_client.register_user(user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_with_invalid_username(self, api_client):
        pass

    @pytest.mark.parametrize("email, status_code", test_data_invalid_email)
    @pytest.mark.asyncio
    async def test_create_user_with_invalid_email(self, api_client, email, status_code):
        user_data = user_data_for_negative_test.copy()
        user_data["email"] = email
        response = await api_client.register_user(user_data)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "password, confirmPassword, status_code, ids",
        test_data_invalid_password,
        ids=[data[3] for data in test_data_invalid_password],
    )
    @pytest.mark.asyncio
    async def test_create_user_with_invalid_passwords(
        self, api_client, password, confirmPassword, status_code, ids, clean_all_users
    ):
        user_data = user_data_for_negative_test.copy()
        user_data["password"] = password
        user_data["confirmPassword"] = confirmPassword

        response = await api_client.register_user(user_data)
        assert response.status_code == status_code
        await clean_all_users(user_data["email"])

    @pytest.mark.asyncio
    async def test_create_user_with_duplicate_field(self, api_client, clean_all_users):
        user_data = {
            "username": "new_user",
            "username": "dupli_user",
            "email": "user@example.com",
            "email": "dupli@example.com",
            "password": "Password123",
            "password": "Password1234",
            "confirmPassword": "Password1234",
            "notifications": {"email": False, "push": False, "newsletter": False},
        }

        response = await api_client.register_user(user_data)
        assert response.status_code == 201
        assert response.json()["user"]["username"] == "dupli_user"
        assert response.json()["user"]["email"] == "dupli@example.com"
        await clean_all_users(response.json()["user"]["email"])
