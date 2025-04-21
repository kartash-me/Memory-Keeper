from flask import Flask, redirect, render_template
from flask_login import LoginManager, login_required, logout_user

from data import db_session
from data.users import User
from forms import EmailStepForm, FinalStepForm, LoginForm, PhoneStepForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/memory_keeper.db")


@login_manager.user_loader
def load_user(user_id):
    db = db_session.create_session()
    return db.get(User, int(user_id))


@app.route("/")
def index():
    return render_template("base.html", title="Memory Keeper")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    return render_template("login.html", title="Вход", form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    forms = {"0": PhoneStepForm(), "1": EmailStepForm(), "2": FinalStepForm()}
    form = forms.get("0")

    if form.validate_on_submit():
        form = forms.get(form.step.data)

    return render_template("register.html", title="Регистрация", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


if __name__ == "__main__":
    app.run()
