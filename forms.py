from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo
from mega_validators import *


class PhoneStepForm(FlaskForm):
    number = StringField(
        "Номер телефона",
        validators=[
            DataRequired(message="Пожалуйста, введите номер телефона"),
            validate_phone,
            validate_phone_unique
        ]
    )
    step = HiddenField(default="1")
    submit = SubmitField("Далее")


class EmailStepForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Пожалуйста, введите Email"),
            Email(message="Введите корректный Email"),
            validate_email_unique
        ]
    )
    step = HiddenField(default="2")
    submit = SubmitField("Далее")


class FinalStepForm(FlaskForm):
    login = StringField(
        "Логин",
        validators=[
            DataRequired(message="Пожалуйста, введите логин")
        ]
    )
    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(message="Пожалуйста, введите пароль"),
            validate_password
        ]
    )
    password_again = PasswordField(
        "Повторите пароль",
        validators=[
            DataRequired(message="Пожалуйста, повторите пароль"),
            EqualTo("password", message="Пароли не совпадают")
        ]
    )
    step = HiddenField(default="3")
    submit = SubmitField("Зарегистрироваться")


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Пожалуйста, введите Email"),
            Email(message="Введите корректный Email")
        ]
    )
    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(message="Пожалуйста, введите пароль")
        ]
    )
    submit = SubmitField("Войти")
