import random
import string
import time


def generate_password(
    length: int = 12,
    use_uppercase: bool = True,
    use_lowercase: bool = True,
    use_digits: bool = True,
    use_special: bool = True,
    special_chars: str = "!@#$%^&*",
) -> str:
    """Генерирует пароль по заданным правилам."""

    chars = ""
    required = []

    if use_uppercase:
        chars += string.ascii_uppercase
        required.append(random.choice(string.ascii_uppercase))

    if use_lowercase:
        chars += string.ascii_lowercase
        required.append(random.choice(string.ascii_lowercase))

    if use_digits:
        chars += string.digits
        required.append(random.choice(string.digits))

    if use_special:
        chars += special_chars
        required.append(random.choice(special_chars))

    if not chars:
        raise ValueError("Хотя бы один тип символов должен быть включён")

    remaining_length = length - len(required)
    password_chars = required + [random.choice(chars) for _ in range(remaining_length)]

    random.shuffle(password_chars)

    return "".join(password_chars)


def generate_email() -> str:
    return f"autotest_{time.time()}@test.com"
