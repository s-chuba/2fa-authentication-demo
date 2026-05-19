from password_auth import check_password
from totp_auth import verify_totp
from user_db import get_user

def authenticate(username: str, password: str, otp_code: str | None) -> dict:
    # Виконує двофакторну автентифікацію користувача.
    user = get_user(username)

    if user is None:
        return {
            "access": False,
            "reason": "Користувача не знайдено"
        }
    password_is_valid = check_password(password, user["password_hash"])

    if not password_is_valid:
        return {
            "access": False,
            "reason": "Неправильний пароль"
        }

    otp_is_valid, otp_reason = verify_totp(
        secret=user["totp_secret"],
        user_code=otp_code,
        used_codes=user["used_totp_codes"]
    )
    if not otp_is_valid:
        return {
            "access": False,
            "reason": otp_reason
        }
    return {
        "access": True,
        "reason": "Пароль і TOTP-код підтверджено"
    }