from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


data_required = DataRequired(message="Это поле обязательное")
email_check = Email(message="Введите корректный email")
equal_to = EqualTo("password", message="Пароли должны совпадать")


class PhoneStepForm(FlaskForm):
    number = StringField("Номер телефона", validators=[data_required, Length(min=10, max=15)])
    submit = SubmitField("Далее")


class EmailStepForm(FlaskForm):
    email = StringField("Email", validators=[data_required, email_check])
    submit = SubmitField("Далее")


class FinalStepForm(FlaskForm):
    login = StringField("Логин", validators=[data_required])
    password = PasswordField("Пароль", validators=[data_required])
    password_again = PasswordField("Повторите пароль", validators=[data_required, equal_to])
    submit = SubmitField("Зарегистрироваться")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[data_required])
    password = PasswordField("Пароль", validators=[data_required])
    submit = SubmitField("Войти")
