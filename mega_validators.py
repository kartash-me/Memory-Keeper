import re

from flask_login import current_user
from wtforms.validators import ValidationError

from data.db_session import create_session
from data.users import User


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def detect_login_type(identifier: str):
    identifier = identifier.strip()

    if re.fullmatch(r"[^@]+@[^@]+\.[^@]+", identifier):
        return "email"
    if re.fullmatch(r"\+?[\d\-() ]{10,}", identifier):
        return "phone"

    return "login"


def validate_login(_, field):
    login = field.data
    if len(login) < 4:
        raise ValidationError("Логин должен содержать минимум 4 символа")

    if not re.fullmatch(r"^[a-zA-Z0-9_-]+$", login):
        raise ValidationError("Логин может содержать только латинские буквы, цифры и знак подчёркивания")


def validate_phone(_, field):
    phone = field.data.strip()
    cleaned = re.sub(r"[\s()\-–]", "", phone)

    if not (cleaned.startswith("+7") or cleaned.startswith("8")):
        raise ValidationError("Номер должен начинаться с +7 или 8")

    expected_length = 12 if cleaned.startswith("+7") else 11
    if len(cleaned) != expected_length:
        raise ValidationError(f"Длина номера должна быть {expected_length} символов")

    if not cleaned.lstrip("+").isdigit():
        raise ValidationError("Номер содержит недопустимые символы")

    if "--" in phone:
        raise ValidationError("Не допускается два дефиса подряд")

    if phone.startswith("-") or phone.endswith("-"):
        raise ValidationError("Номер не может начинаться или заканчиваться дефисом")

    if phone.count("(") != phone.count(")"):
        raise ValidationError("Количество открывающих и закрывающих скобок должно совпадать")

    if "(" in phone and not re.search(r"\(\d{3}\)", phone):
        raise ValidationError("Скобки должны окружать ровно три цифры")


def validate_password(_, field):
    pwd = field.data or ""
    low = pwd.lower()

    if "yandex" not in low:
        raise ValidationError("Пароль должен содержать слово 'yandex'")
    if pwd.isdigit():
        raise ValidationError("Пароль не может быть просто числом")
    if len(pwd) <= 8:
        raise ValidationError("Пароль должен быть длиннее 8 символов")
    if not any(c.isdigit() for c in pwd):
        raise ValidationError("Пароль должен содержать хотя бы одну цифру")
    if not any(c.isupper() for c in pwd):
        raise ValidationError("Пароль должен содержать заглавную букву")
    if not any(c.islower() for c in pwd):
        raise ValidationError("Пароль должен содержать строчную букву")

    keyboard_rows = ["qwertyuiop", "йцукенгшщзхъё", "asdfghjkl", "фывапролджэё", "zxcvbnm", "ячсмитьбю"]
    for row in keyboard_rows:
        for i in range(len(row) - 2):
            if row[i:i + 3] in low:
                raise ValidationError("Пароль содержит простую последовательность клавиш")


def validate_phone_unique(_, field):
    db = create_session()
    cleaned = normalize_phone(field.data)
    user = db.query(User).filter(User.number == cleaned).first()
    if user and (not current_user.is_authenticated or user.id != current_user.id):
        raise ValidationError("Пользователь с таким номером уже зарегистрирован")


def validate_email_unique(_, field):
    db = create_session()
    exists = db.query(User).filter(User.email == field.data.strip()).first()
    if exists:
        raise ValidationError("Пользователь с таким email уже зарегистрирован")


def validate_login_unique(_, field):
    db = create_session()
    user = db.query(User).filter(User.login == field.data).first()
    if user and (not current_user.is_authenticated or user.id != current_user.id):
        raise ValidationError("Пользователь с таким логином уже зарегестрирован")
