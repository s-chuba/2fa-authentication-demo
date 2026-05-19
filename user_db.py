from password_auth import hash_password

USERS = {
    "sofiia": {
        "password_hash": hash_password("Student123"),
        "totp_secret": "JBSWY3DPEHPK3PXP",
        "used_totp_codes": set()
    }
}

def get_user(username: str):
    # Повертає дані користувача за логіном.  Якщо користувача не знайдено, повертає None.
    return USERS.get(username)

def reset_used_codes(username: str) -> None:
    # Очищує список використаних TOTP-кодів для повторного запуску експериментів.
    user = get_user(username)

    if user:
        user["used_totp_codes"].clear()