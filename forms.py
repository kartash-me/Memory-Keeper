from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DateTimeField,
    FileField,
    HiddenField,
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Optional

from mega_validators import (
    validate_email_unique,
    validate_login,
    validate_login_unique,
    validate_password,
    validate_phone,
    validate_phone_unique,
)


class PhoneStepForm(FlaskForm):
    number = StringField(
        "Номер телефона",
        validators=[
            DataRequired(message="Пожалуйста, введите номер телефона"),
            validate_phone,
            validate_phone_unique,
        ],
    )
    submit = SubmitField("Далее")


class EmailStepForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Пожалуйста, введите Email"),
            Email(message="Введите корректный Email"),
            validate_email_unique,
        ],
    )
    submit = SubmitField("Далее")


class FinalStepForm(FlaskForm):
    login = StringField(
        "Логин",
        validators=[
            DataRequired(message="Пожалуйста, введите логин"),
            validate_login,
            validate_login_unique,
        ],
    )
    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(message="Пожалуйста, введите пароль"),
            validate_password,
        ],
    )
    password_again = PasswordField(
        "Повторите пароль",
        validators=[
            DataRequired(message="Пожалуйста, повторите пароль"),
            EqualTo("password", message="Пароли не совпадают"),
        ],
    )
    submit = SubmitField("Зарегистрироваться")


class LoginForm(FlaskForm):
    identifier = StringField(
        "Email / Логин / Телефон",
        validators=[
            DataRequired(message="Пожалуйста, введите Email, логин или телефон")
        ],
    )
    password = PasswordField(
        "Пароль", validators=[DataRequired(message="Пожалуйста, введите пароль")]
    )
    submit = SubmitField("Войти")


class AccountForm(FlaskForm):
    name = StringField("Имя")
    surname = StringField("Фамилия")
    date_of_birth = DateField("Дата рождения", validators=[Optional()])
    login = StringField(
        "Логин",
        validators=[
            DataRequired(message="Пожалуйста, введите логин"),
            validate_login,
            validate_login_unique,
        ],
    )
    email = StringField("Email")
    number = StringField("Номер телефона")
    submit = SubmitField("Сохранить")


class AvatarForm(FlaskForm):
    avatar = FileField("Аватар", render_kw={"accept": "image/*"})


class UploadPhotoForm(FlaskForm):
    file = FileField("Фото", render_kw={"accept": "image/*"})
    address = StringField("Адрес", validators=[Optional()])
    taken_at = DateTimeField(
        "Время съёмки", format="%d.%m.%Y %H:%M:%S", validators=[Optional()]
    )
    description = StringField("Описание", validators=[Optional()])
    latitude = HiddenField()
    longitude = HiddenField()
    submit = SubmitField("Готово")
