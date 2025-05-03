import os

from flask import (
    Flask, abort, flash, redirect, render_template, send_from_directory,
    session, url_for
)
from flask_login import (
    LoginManager, current_user, login_required, login_user, logout_user
)

from data import db_session
from data.users import User
from forms import EmailStepForm, FinalStepForm, LoginForm, PhoneStepForm


app = Flask(__name__)
app.config["MEDIA_URL"] = "media"
app.config["SECRET_KEY"] = "your_secret_key"
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024 * 1024
app.config["ALLOWED_EXTENSIONS"] = [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico"]

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/memory_keeper.db")


def get_avatar_url(user):
    if user.avatar:
        return url_for("media", user=user.login, filename=user.avatar)
    return url_for("static", filename="img/userpic.png")


app.jinja_env.globals["avatar"] = get_avatar_url


def save(file, user):
    directory = str(os.path.join(app.config["MEDIA_URL"], user))

    if not os.path.exists(directory):
        os.makedirs(directory)

    n = 0
    filename = file.filename # добавить нормализацию имени файла
    name, ext = os.path.splitext(filename)

    if ext not in app.config["ALLOWED_EXTENSIONS"]:
        raise ValueError("Такой файл не поддерживается")

    while os.path.exists(os.path.join(directory, filename)):
        filename = f"{name}_{n}{ext}"
        n += 1

    file.save(os.path.join(directory, filename))
    return filename


@login_manager.user_loader
def load_user(user_id):
    db = db_session.create_session()
    return db.get(User, int(user_id))


@app.route("/<user>/<filename>")
@login_required
def media(user, filename):
    if current_user.login == user:
        directory = str(os.path.join(app.config["MEDIA_URL"], user))
        return send_from_directory(directory, filename)

    abort(403)


@app.route("/")
def index():
    return render_template("promotion/index.html", title="Memory Keeper")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()
    if form.validate_on_submit():
        db = db_session.create_session()
        user = db.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("home"))
        flash("Неверный email или пароль", "error")

    return render_template("promotion/form.html", title="Авторизация", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    step = session.get("step", 0)
    forms = [PhoneStepForm(), EmailStepForm(), FinalStepForm()]
    form = forms[step]

    if form.validate_on_submit():
        # Шаг 0: сохраняем телефон
        if step == 0:
            session["number"] = form.number.data
            session["step"] = 1
            return redirect(url_for("register"))

        # Шаг 1: сохраняем email
        if step == 1:
            session["email"] = form.email.data
            session["step"] = 2
            return redirect(url_for("register"))

        # Шаг 2: финальная регистрация
        if step == 2:
            db = db_session.create_session()

            # Проверяем уникальность email
            if db.query(User).filter(User.email == session["email"]).first():
                flash("Пользователь с таким email уже зарегистрирован", "error")
                return render_template(
                    "promotion/form.html", title="Регистрация", form=form
                )

            # Проверяем уникальность номера
            if db.query(User).filter(User.number == session["number"]).first():
                flash("Пользователь с таким номером уже зарегистрирован", "error")
                return render_template(
                    "promotion/form.html", title="Регистрация", form=form
                )

            user = User(
                number=session["number"], email=session["email"], login=form.login.data
            )
            user.set_password(form.password.data)
            db.add(user)
            db.commit()

            login_user(user)
            session.clear()
            return redirect(url_for("home"))

    return render_template("promotion/form.html", title="Регистрация", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/home")
@login_required
def home():
    return render_template("main/home.html", title="Memory Keeper")


@app.route("/profile")
@login_required
def profile():
    return render_template("main/profile.html", title="Профиль")


if __name__ == "__main__":
    app.run(debug=True)
