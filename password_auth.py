import hashlib

SALT = "2fa_demo_salt"

def hash_password(password: str) -> str:
    """
    Формує хеш пароля з додаванням солі.
    У тестовому середовищі це використовується замість зберігання пароля у відкритому вигляді.
    """
    password_with_salt = password + SALT
    return hashlib.sha256(password_with_salt.encode("utf-8")).hexdigest()

def check_password(input_password: str, stored_password_hash: str) -> bool:
    # Перевіряє, чи відповідає введений пароль збереженому хешу.
    return hash_password(input_password) == stored_password_hash