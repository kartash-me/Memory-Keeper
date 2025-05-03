from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
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
    submit = SubmitField("Далее")


class FinalStepForm(FlaskForm):
    login = StringField(
        "Логин",
        validators=[
            DataRequired(message="Пожалуйста, введите логин"),
            validate_login
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
    submit = SubmitField("Зарегистрироваться")


class LoginForm(FlaskForm):
    identifier = StringField(
        "Email / Логин / Телефон",
        validators=[DataRequired(message="Пожалуйста, введите Email, логин или телефон")]
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired(message="Пожалуйста, введите пароль")]
    )
    submit = SubmitField("Войти")
