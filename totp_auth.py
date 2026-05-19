import base64
import hashlib
import hmac
import struct
import time

def generate_totp(secret: str, for_time: int | None = None, interval: int = 30, digits: int = 6) -> str:
    """
    Генерує TOTP-код на основі секретного ключа та поточного часу.
    За замовчуванням код змінюється кожні 30 секунд.
    """
    if for_time is None:
        for_time = int(time.time())

    counter = int(for_time // interval)

    secret_bytes = base64.b32decode(secret, casefold=True)
    counter_bytes = struct.pack(">Q", counter)

    hmac_hash = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()

    offset = hmac_hash[-1] & 0x0F

    binary_code = struct.unpack(">I", hmac_hash[offset:offset + 4])[0] & 0x7FFFFFFF
    otp_code = binary_code % (10 ** digits)

    return str(otp_code).zfill(digits)

def verify_totp(
    secret: str,
    user_code: str,
    used_codes: set,
    valid_window: int = 1,
    interval: int = 30,
    digits: int = 6
) -> tuple[bool, str]:
    # Перевіряє TOTP-код користувача.
    if user_code is None or user_code == "":
        return False, "TOTP-код не введено"

    if not user_code.isdigit() or len(user_code) != digits:
        return False, "TOTP-код має містити 6 цифр"

    current_time = int(time.time())

    for offset in range(-valid_window, valid_window + 1):
        check_time = current_time + offset * interval
        expected_code = generate_totp(secret, for_time=check_time, interval=interval, digits=digits)
        counter = int(check_time // interval)

        code_id = f"{expected_code}:{counter}"

        if user_code == expected_code:
            if code_id in used_codes:
                return False, "TOTP-код уже був використаний"

            used_codes.add(code_id)
            return True, "TOTP-код підтверджено"

    return False, "TOTP-код неправильний або прострочений"