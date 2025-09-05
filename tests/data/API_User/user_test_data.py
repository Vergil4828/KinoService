class CreateUserData:
    # ПЕРЕПИСАТЬ С РАНДОМОМ
    base_user_data = {
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

    positive_test_data = [
        (
            "new_user",
            "user@example.com",
            "Password123",
            "Password123",
            False,
            "Standard user_data",
        ),
        (
            "n",
            "user@example.com",
            "Password",
            "Password",
            True,
            "Minimum password and username length",
        ),
        (
            "n" * 50,
            "user@example.com",
            "P" * 72,
            "P" * 72,
            True,
            "Maximum password and username length",
        ),
    ]
    test_data_valid_username = [
        ("user123", 201, "valid_alphanumeric"),
        ("user-name", 201, "valid_with_dash"),
        ("user_name", 201, "valid_with_underscore"),
        ("User_Name-123", 201, "valid_mixed_case"),
        ("a", 201, "valid_single_char"),
        ("test-user_123", 201, "valid_complex"),
        ("usuario", 201, "latin_username"),
        ("ABC123", 201, "uppercase_letters"),
        ("test123_name-user", 201, "complex_valid_username"),
        ("n" * 50, 201, "maximum_username_length"),
    ]
    test_data_valid_email = [
        ("user.name@example.com", 201, "valid_dot_in_local"),
        ("user+tag@example.com", 201, "valid_plus_in_local"),
        ("user-name@example.com", 201, "valid_dash_in_local"),
        ("user_name@example.com", 201, "valid_underscore_in_local"),
        ("user123@example.com", 201, "valid_numbers_in_local"),
        ("test@domain-name.com", 201, "valid_dash_in_domain"),
        ("user@sub.domain.com", 201, "valid_subdomain"),
        ("a" * 64 + "@example.com", 201, "maximum_local_part_length"),
        ("user@" + "a" * 63 + ".com", 201, "maximum_domain_length"),
    ]
    test_data_valid_password = [
        ("12345678", 201, "minimum_8_digits"),
        ("password", 201, "minimum_8_letters"),
        ("Password123", 201, "mixed_case_with_numbers"),
        ("Pass@123", 201, "password_with_at_symbol"),
        ("Test$456", 201, "password_with_dollar_symbol"),
        ("User!Pass", 201, "password_with_exclamation"),
        ("a" * 72, 201, "long_50_character_password"),
        ("My Pass 8", 201, "password_with_space"),
        ("Пароль123", 201, "cyrillic_password"),
        ("SecureP@ss2024!", 201, "complex_password_all_types"),
    ]

    test_data_invalid_username = [
        ("", 422, "Empty username"),
        ("        ", 422, "Spaces in the username"),
        (1234, 422, "Number in the username"),
        (False, 422, "Bool in the username"),
        (True, 422, "Bool in the username"),
        (None, 422, "None in the username"),
        ("user@name", 422, "at_symbol_in_username"),
        ("user#name", 422, "hash_symbol_in_username"),
        ("user$name", 422, "dollar_symbol_in_username"),
        ("user%name", 422, "percent_symbol_in_username"),
        ("user&name", 422, "ampersand_in_username"),
        ("user*name", 422, "asterisk_in_username"),
        ("user+name", 422, "plus_in_username"),
        ("user=name", 422, "equals_in_username"),
        ("user!name", 422, "exclamation_in_username"),
        ("user?name", 422, "question_mark_in_username"),
        ("user name", 422, "space_in_username"),
        ("user.name", 422, "dot_in_username"),
        ("user,name", 422, "comma_in_username"),
        ("user;name", 422, "semicolon_in_username"),
        ("user:name", 422, "colon_in_username"),
        ("user'name", 422, "apostrophe_in_username"),
        ('user"name', 422, "quote_in_username"),
        ("user\\name", 422, "backslash_in_username"),
        ("user/name", 422, "forward_slash_in_username"),
        ("user|name", 422, "pipe_in_username"),
        ("user<name", 422, "less_than_in_username"),
        ("user>name", 422, "greater_than_in_username"),
        ("user[name]", 422, "brackets_in_username"),
        ("user{name}", 422, "braces_in_username"),
        ("user(name)", 422, "parentheses_in_username"),
        ("user~name", 422, "tilde_in_username"),
        ("user`name", 422, "backtick_in_username"),
        ("пользователь", 422, "cyrillic_username"),
        ("用户名", 422, "chinese_username"),
        ("ユーザー", 422, "japanese_username"),
        ("-username", 422, "starts_with_dash"),
        ("username-", 422, "ends_with_dash"),
        ("_username", 422, "starts_with_underscore"),
        ("username_", 422, "ends_with_underscore"),
        ("user--name", 422, "double_dash"),
        ("user__name", 422, "double_underscore"),
        ("user-_name", 422, "dash_underscore"),
        ("user_-name", 422, "underscore_dash"),
        ("n" * 51, 422, "maximum_username_length"),
        ("<script>alert('xss')</script>", 422, "xss_script_username"),
        ("'; DROP TABLE transactions; --", 422, "sql_injection_username"),
        ("../../../etc/passwd", 422, "path_traversal_username"),
    ]

    test_data_invalid_email = [
        ("", 422, "Empty email"),
        ("user@example", 422, "Invalid email"),
        ("userexample.com", 422, "Invalid email"),
        ("user@", 422, "Invalid email"),
        ("@example.com", 422, "Invalid email"),
        ("user@exam$ple.com", 422, "dollar_in_domain"),
        ("usertest@exam%ple.com", 422, "percent_in_domain"),
        ("username@exam&ple.com", 422, "ampersand_in_domain"),
        ("usertag@exam#ple.com", 422, "hash_in_domain"),
        ("username@exam*ple.com", 422, "asterisk_in_domain"),
        ("username@exam=ple.com", 422, "equals_in_domain"),
        (".user@example.com", 422, "starts_with_dot"),
        ("user.@example.com", 422, "ends_with_dot"),
        ("us..er@example.com", 422, "double_dots"),
        ("a" * 65 + "@example.com", 422, "local_part_too_long"),
        ("user@" + "a" * 64 + ".com", 422, "domain_too_long"),
        (1234567, 422, "Number in the email"),
        (False, 422, "Bool in the email"),
        (True, 422, "Bool in the email"),
    ]

    test_data_invalid_password = [
        ("", "Password123", 422, "password is empty"),
        ("Password123", "", 422, "confirmPassword is empty"),
        ("Password123", "Password1234", 422, "Password do not match"),
        ("Passwor", "Passwor", 422, "Password length < 8"),
        (
            "   Passwo",
            "          Passwo      ",
            422,
            "Spaces in the password",
        ),
        ("p" * 73, "p" * 73, 422, "maximum_password_lenght"),
        (12345678, 12345678, 422, "Only numbers in the passwords"),
        (True, True, 422, "Bool [T,T] in the passwords"),
        (False, False, 422, "Bool [F,F] in the passwords"),
        (True, False, 422, "Bool [T,F] in the passwords"),
        (False, True, 422, "Bool [F,T] in the passwords"),
        (None, None, 422, "None in the passwords"),
    ]

    test_data_invalid_notifications = [
        ("email", 10, 422, "number_in_email_notification"),
        ("email", None, 422, "none_in_email_notification"),
        ("email", "asd", 422, "string_in_email_notification"),
        ("push", 10, 422, "number_in_email_notification"),
        ("push", None, 422, "none_in_email_notification"),
        ("push", "asd", 422, "string_in_email_notification"),
        ("newsletter", 10, 422, "number_in_email_notification"),
        ("newsletter", None, 422, "none_in_email_notification"),
        ("newsletter", "asd", 422, "string_in_email_notification"),
    ]


class LoginUserData:
    base_credential = {
        "email": "user@example.com",
        "password": "Password123",
    }

    positive_test_data = [
        ("user@example.com", "Password123", 200, "Standard user data"),
        ("user@example.com", "Password", 200, "Minimum password length"),
    ]

    test_data_valid_email = CreateUserData.test_data_valid_email.copy()

    test_data_valid_password = [
        ("12345678", 200, "minimum_8_digits"),
        ("password", 200, "minimum_8_letters"),
        ("Password123", 200, "mixed_case_with_numbers"),
        ("Pass@123", 200, "password_with_at_symbol"),
        ("Test$456", 200, "password_with_dollar_symbol"),
        ("User!Pass", 200, "password_with_exclamation"),
        ("a" * 72, 200, "long_50_character_password"),
        ("My Pass 8", 200, "password_with_space"),
        ("Пароль123", 200, "cyrillic_password"),
        ("SecureP@ss2024!", 200, "complex_password_all_types"),
    ]

    test_data_invalid_email = CreateUserData.test_data_invalid_email.copy()
    test_data_invalid_password = [
        ("", 422, "password is empty"),
        ("Passwor", 422, "Password length < 8"),
        (
            "   Passwo",
            422,
            "Spaces in the password",
        ),
        ("p" * 73, 422, "maximum_password_length"),
        (12345678, 422, "Only numbers in the password"),
        (True, 422, "Bool in the password"),
        (False, 422, "Bool in the password"),
        (None, 422, "None in the password"),
    ]


class UpdateUserData:
    base_user_update_data = {
        "username": "new_user",
        "email": "user@example.com",
        "newPassword": "Password123",
        "currentPassword": "Password123",
    }

    test_data_valid_username = [
        ("user123", 201, "valid_alphanumeric"),
        ("user-name", 201, "valid_with_dash"),
        ("user_name", 201, "valid_with_underscore"),
        ("User_Name-123", 201, "valid_mixed_case"),
        ("a", 201, "valid_single_char"),
        ("test-user_123", 201, "valid_complex"),
        ("usuario", 201, "latin_username"),
        ("ABC123", 201, "uppercase_letters"),
        ("test123_name-user", 201, "complex_valid_username"),
        ("n" * 50, 201, "maximum_username_length"),
        (None, 422, "None in the username"),
    ]
    test_data_valid_email = CreateUserData.test_data_valid_email.copy()
    test_data_valid_new_password = [
        ("12345678", 200, "minimum_8_digits"),
        ("password", 200, "minimum_8_letters"),
        ("Password123", 200, "mixed_case_with_numbers"),
        ("Pass@123", 200, "password_with_at_symbol"),
        ("Test$456", 200, "password_with_dollar_symbol"),
        ("User!Pass", 200, "password_with_exclamation"),
        ("a" * 72, 200, "long_50_character_password"),
        ("My Pass 8", 200, "password_with_space"),
        ("Пароль123", 200, "cyrillic_password"),
        ("SecureP@ss2024!", 200, "complex_password_all_types"),
        (None, 200, "none_in_new_password"),
    ]
    test_data_valid_current_password = LoginUserData.test_data_valid_password.copy()

    test_data_invalid_username = [
        ("", 422, "Empty username"),
        ("        ", 422, "Spaces in the username"),
        (1234, 422, "Number in the username"),
        (False, 422, "Bool in the username"),
        (True, 422, "Bool in the username"),
        ("user@name", 422, "at_symbol_in_username"),
        ("user#name", 422, "hash_symbol_in_username"),
        ("user$name", 422, "dollar_symbol_in_username"),
        ("user%name", 422, "percent_symbol_in_username"),
        ("user&name", 422, "ampersand_in_username"),
        ("user*name", 422, "asterisk_in_username"),
        ("user+name", 422, "plus_in_username"),
        ("user=name", 422, "equals_in_username"),
        ("user!name", 422, "exclamation_in_username"),
        ("user?name", 422, "question_mark_in_username"),
        ("user name", 422, "space_in_username"),
        ("user.name", 422, "dot_in_username"),
        ("user,name", 422, "comma_in_username"),
        ("user;name", 422, "semicolon_in_username"),
        ("user:name", 422, "colon_in_username"),
        ("user'name", 422, "apostrophe_in_username"),
        ('user"name', 422, "quote_in_username"),
        ("user\\name", 422, "backslash_in_username"),
        ("user/name", 422, "forward_slash_in_username"),
        ("user|name", 422, "pipe_in_username"),
        ("user<name", 422, "less_than_in_username"),
        ("user>name", 422, "greater_than_in_username"),
        ("user[name]", 422, "brackets_in_username"),
        ("user{name}", 422, "braces_in_username"),
        ("user(name)", 422, "parentheses_in_username"),
        ("user~name", 422, "tilde_in_username"),
        ("user`name", 422, "backtick_in_username"),
        ("пользователь", 422, "cyrillic_username"),
        ("用户名", 422, "chinese_username"),
        ("ユーザー", 422, "japanese_username"),
        ("-username", 422, "starts_with_dash"),
        ("username-", 422, "ends_with_dash"),
        ("_username", 422, "starts_with_underscore"),
        ("username_", 422, "ends_with_underscore"),
        ("user--name", 422, "double_dash"),
        ("user__name", 422, "double_underscore"),
        ("user-_name", 422, "dash_underscore"),
        ("user_-name", 422, "underscore_dash"),
        ("n" * 51, 422, "maximum_username_length"),
        ("<script>alert('xss')</script>", 422, "xss_script_username"),
        ("'; DROP TABLE transactions; --", 422, "sql_injection_username"),
        ("../../../etc/passwd", 422, "path_traversal_username"),
    ]
    test_data_invalid_email = CreateUserData.test_data_invalid_email.copy()
    test_data_invalid_new_password = [
        ("", 422, "password is empty"),
        ("Passwor", 422, "Password length < 8"),
        (
            "   Passwo",
            422,
            "Spaces in the password",
        ),
        ("p" * 73, 422, "maximum_password_length"),
        (12345678, 422, "Only numbers in the password"),
        (True, 422, "Bool in the password"),
        (False, 422, "Bool in the password"),
    ]
    test_data_invalid_current_password = LoginUserData.test_data_invalid_password.copy()
