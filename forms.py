from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
import re

from data.db_session import create_session
from data.users import User


class PhoneValidator:
    def __call__(self, form, field):
        phone = field.data.strip()
        if not (phone.startswith('+7') or phone.startswith('8')):
            raise ValidationError("Номер должен начинаться с +7 или 8")
        phone_no_spaces = phone.replace(' ', '')
        left_paren = phone_no_spaces.count('(')
        right_paren = phone_no_spaces.count(')')
        if left_paren != right_paren or left_paren > 1:
            raise ValidationError("Допускается только одна пара скобок")
        if left_paren and not re.search(r'\(\d{3}\)', phone_no_spaces):
            raise ValidationError("Скобки должны окружать три цифры")
        if '--' in phone_no_spaces:
            raise ValidationError("Не допускается два дефиса подряд")
        if phone_no_spaces.startswith('-') or phone_no_spaces.endswith('-'):
            raise ValidationError("Номер не может начинаться или заканчиваться дефисом")
        cleaned = re.sub(r'[\s()\-\–]', '', phone)  # убираем пробелы, скобки, дефисы
        if phone.startswith('+'):
            if not cleaned[1:].isdigit():
                raise ValidationError("Номер содержит недопустимые символы")
        else:
            if not cleaned.isdigit():
                raise ValidationError("Номер содержит недопустимые символы")


def validate_password(_, field):
    pwd = field.data or ''
    if 'yandex' in pwd.lower():
        raise ValidationError("Пароль не должен содержать слово 'yandex'")
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
    keyboard_rows = ['qwertyuiop', 'йцукенгшщзхъё', 'asdfghjkl', 'фывапролджэё', 'zxcvbnm', 'ячсмитьбю']
    low = pwd.lower()
    for row in keyboard_rows:
        for i in range(len(row) - 2):
            if row[i:i+3] in low:
                raise ValidationError("Пароль содержит простую последовательность клавиш")


def validate_phone_unique(_, field):
    db = create_session()
    cleaned = re.sub(r'[\s()\-\–]', '', field.data.strip())
    exists = db.query(User).filter(User.number == cleaned).first()
    if exists:
        raise ValidationError("Пользователь с таким номером уже зарегистрирован")


def validate_email_unique(_, field):
    db = create_session()
    exists = db.query(User).filter(User.email == field.data).first()
    if exists:
        raise ValidationError("Пользователь с таким email уже зарегистрирован")


class PhoneStepForm(FlaskForm):
    number = StringField(
        'Номер телефона',
        validators=[DataRequired(), PhoneValidator(), validate_phone_unique]
    )
    step = HiddenField(default='1')
    submit = SubmitField('Далее')


class EmailStepForm(FlaskForm):
    email = StringField(
        'Email',
        validators=[DataRequired(), Email('Некорректный email'), validate_email_unique]
    )
    step = HiddenField(default='2')
    submit = SubmitField('Далее')


class FinalStepForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired(), validate_password])
    password_again = PasswordField(
        'Повторите пароль',
        validators=[DataRequired(), EqualTo('password', message='Пароли не совпадают')]
    )
    step = HiddenField(default='3')
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email('Некорректный email')])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')
