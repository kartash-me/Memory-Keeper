from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class PhoneStepForm(FlaskForm):
    number = StringField("Номер телефона", validators=[DataRequired(), Length(min=10, max=15)])
    step = HiddenField(default='1')
    submit = SubmitField("Далее")

class EmailStepForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    step = HiddenField(default='2')
    submit = SubmitField("Далее")

class FinalStepForm(FlaskForm):
    login = StringField("Логин", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    password_again = PasswordField("Повторите пароль", validators=[DataRequired(),
                                                    EqualTo('password', message="Пароли должны совпадать")])
    step = HiddenField(default='3')
    submit = SubmitField("Зарегистрироваться")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")
