import base64
import os
import re

from flask import (
    Flask, abort, flash, redirect, render_template, send_from_directory,
    session, url_for
)
from flask_login import (
    LoginManager, current_user, login_required, login_user, logout_user
)
from transliterate import translit
from werkzeug.utils import secure_filename

from data import db_session
from data.users import User
from forms import (
    AvatarForm, EmailStepForm, FinalStepForm, LoginForm, PhoneStepForm, ProfileForm,
    detect_login_type
)


app = Flask(__name__)
app.config["MEDIA_URL"] = "media"
app.config["SECRET_KEY"] = "your_secret_key"
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024 ** 2
app.config["ALLOWED_EXTENSIONS"] = [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico"]

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/memory_keeper.db")


def save_avatar(file, user):
    encoded_image = base64.b64encode(file.read()).decode("ascii")

    with db_session.create_session() as db:
        user.avatar = encoded_image
        db.merge(user)
        db.commit()


def get_avatar(user):
    if user.avatar:
        return "data:image/png;base64," + user.avatar
    return url_for("static", filename="img/userpic.png")


app.jinja_env.globals["avatar"] = get_avatar


def normalize_filename(filename):
    name, ext = os.path.splitext(filename)
    name = re.sub(r"[^\w\-]", "", name)
    name = name.replace(" ", "_")
    name = translit(name, "ru", reversed=True)

    return f"{name}{ext}"


def save(file, user):
    directory = str(os.path.join(app.config["MEDIA_URL"], user.id))

    if not os.path.exists(directory):
        os.makedirs(directory)

    n = 0
    filename = secure_filename(normalize_filename(file.filename))
    path = os.path.join(directory, filename)
    name, ext = os.path.splitext(filename)

    if ext not in app.config["ALLOWED_EXTENSIONS"]:
        raise ValueError("Такой файл не поддерживается")

    while os.path.exists(path):
        filename = f"{name}_{n}{ext}"
        path = os.path.join(directory, filename)
        n += 1

    file.save(path)
    return filename


@login_manager.user_loader
def load_user(user_id):
    db = db_session.create_session()
    return db.get(User, int(user_id))


@app.route("/<user>/<filename>")
@login_required
def media(user, filename):
    if current_user.id == user.id:
        directory = str(os.path.join(app.config["MEDIA_URL"], user.id))
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
        identifier = form.identifier.data.strip()
        login_type = detect_login_type(identifier)
        user: User | None = None

        if login_type == "email":
            user = db.query(User).filter(User.email == identifier).first()
        elif login_type == "phone":
            cleaned = re.sub(r"[\s()\-–]", "", identifier)
            user = db.query(User).filter(User.number == cleaned).first()
        elif login_type == "login":
            user = db.query(User).filter(User.login == identifier).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("home"))

        flash("Неверные данные для входа", "error")

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
                return render_template("promotion/form.html", title="Регистрация", form=form)

            # Проверяем уникальность номера
            if db.query(User).filter(User.number == session["number"]).first():
                flash("Пользователь с таким номером уже зарегистрирован", "error")
                return render_template("promotion/form.html", title="Регистрация", form=form)

            user = User(number=session["number"], email=session["email"], login=form.login.data)
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


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()
    avatar_form = AvatarForm()

    if form.submit.data:
        if form.validate_on_submit():
            form_data, user_data = form.data, current_user.__dict__

            with db_session.create_session() as db:
                for field in form_data.keys() & user_data.keys():
                    if form_data[field] is not None:
                        if form_data[field] != user_data[field] and str(form_data[field]).strip() != "":
                            setattr(current_user, field, form_data[field])

                db.merge(current_user)
                db.commit()
    elif avatar_form.validate_on_submit():
        save_avatar(avatar_form.avatar.data, current_user)

    return render_template("main/profile.html", title="Профиль", form=form, avatar_form=avatar_form)


if __name__ == "__main__":
    app.run(debug=True)
