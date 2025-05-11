from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.utils import secure_filename

from data import db_session
from data.photo import Photo
from data.users import User
from forms import (
    AvatarForm,
    EmailStepForm,
    FinalStepForm,
    LoginForm,
    PhoneStepForm,
    ProfileForm,
    UploadPhotoForm,
)
from functions import *
from mega_validators import detect_login_type, normalize_phone



app = Flask(__name__)
app.config["MEDIA_URL"] = "media"
app.config["SECRET_KEY"] = "your_secret_key"
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024 ** 2
app.config["ALLOWED_EXTENSIONS"] = [".jpg", ".jpeg",
                                    ".png", ".gif", ".svg", ".webp", ".bmp", ".ico"]

app.jinja_env.globals["static"] = static = lambda filename: url_for(
    "static", filename=filename)
app.jinja_env.globals["media"] = media = lambda filename: url_for(
    "get_photo", filename=filename)
app.jinja_env.globals["photo"] = photo = lambda filename: url_for(
    "photo_page", filename=filename)
app.jinja_env.globals["avatar"] = get_avatar

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/memory_keeper.db")


def save(file, user, *,
         latitude=None, longitude=None, address=None,
         timestamp=None, description=None):

    directory = os.path.join(app.config["MEDIA_URL"], str(user.id))
    os.makedirs(directory, exist_ok=True)

    filename = secure_filename(normalize_filename(
        getattr(file, "filename", "uploaded.jpg")))
    path = os.path.join(directory, filename)
    name, ext = os.path.splitext(filename)

    n = 0
    while os.path.exists(path):
        filename = f"{name}_{n}{ext}"
        path = os.path.join(directory, filename)
        n += 1

    if hasattr(file, "stream"):
        file.stream.seek(0)

    with open(path, "wb") as dst:
        dst.write(file.read())

    thumbnail(file, path)

    with db_session.create_session() as db:
        photo_ = Photo(
            filename=filename,
            user_id=user.id,
            latitude=latitude,
            longitude=longitude,
            address=address,
            timestamp=timestamp,
            description=description
        )
        size = os.path.getsize(path)
        user.used_space += size
        db.add(photo_)
        db.commit()


@login_manager.user_loader
def load_user(user_id):
    with db_session.create_session() as db:
        return db.get(User, int(user_id))


@app.route("/")
def index():
    return render_template("promotion/index.html", title="Memory Keeper")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()
    if form.validate_on_submit():
        with db_session.create_session() as db:
            identifier = form.identifier.data.strip()
            login_type = detect_login_type(identifier)
            user: User | None = None

            if login_type == "email":
                user = db.query(User).filter(User.email == identifier).first()
            elif login_type == "phone":
                cleaned = normalize_phone(identifier)
                user = db.query(User).filter(User.number == cleaned).first()
            elif login_type == "login":
                user = db.query(User).filter(User.login == identifier).first()

            if user and user.check_password(form.password.data):
                login_user(user)
                return redirect(url_for("home"))

            flash("Неверные данные для входа", "error")

    return render_template(
        "promotion/form.html",
        title="Авторизация",
        form=form)


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
            session["number"] = normalize_phone(form.number.data)
            session["step"] = 1
            return redirect(url_for("register"))

        # Шаг 1: сохраняем email
        if step == 1:
            session["email"] = form.email.data
            session["step"] = 2
            return redirect(url_for("register"))

        # Шаг 2: финальная регистрация
        if step == 2:
            with db_session.create_session() as db:
                # Проверяем уникальность email
                if db.query(User).filter(
                        User.email == session["email"]).first():
                    flash(
                        "Пользователь с таким email уже зарегистрирован",
                        "error")
                    return render_template(
                        "promotion/form.html", title="Регистрация", form=form)

                # Проверяем уникальность номера
                if db.query(User).filter(
                        User.number == session["number"]).first():
                    flash(
                        "Пользователь с таким номером уже зарегистрирован",
                        "error")
                    return render_template(
                        "promotion/form.html", title="Регистрация", form=form)

                user = User(
                    number=session["number"],
                    email=session["email"],
                    login=form.login.data,
                    date_of_registration=dt.datetime.now()
                )
                user.set_password(form.password.data)
                db.add(user)
                db.commit()
                session.clear()
                login_user(user)
                return redirect(url_for("home"))

    return render_template(
        "promotion/form.html",
        title="Регистрация",
        form=form)


@app.route("/photos_geo")
@login_required
def photos_geo():
    with db_session.create_session() as db:
        photos = (db.query(Photo)
                    .filter(Photo.user_id == current_user.id,
                            Photo.latitude.isnot(None),
                            Photo.longitude.isnot(None))
                    .all())

        data = []
        for p in photos:
            name, ext = os.path.splitext(p.filename)
            thumb = f"{name}_tmb{ext}"

            data.append({
                "lat": p.latitude,
                "lon": p.longitude,
                "thumb": url_for("get_photo", filename=thumb),
                "full": url_for("get_photo", filename=p.filename),
                "address": p.address,
                "timestamp": p.timestamp.isoformat() if p.timestamp else None,
                "description": p.description or ""
            })

    return jsonify(data)


@app.route("/upload_photo", methods=["GET", "POST"])
@login_required
def upload_photo():
    form = UploadPhotoForm()

    if request.method == "POST" and form.file.data:
        file = form.file.data

        preview = make_preview(file)

        tmp_dir = os.path.join("tmp_uploads", str(current_user.id))
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.join(tmp_dir, secure_filename(file.filename))
        file.seek(0)
        file.save(tmp_path)
        session["tmp_path"] = tmp_path

        # EXIF-мета
        meta = extract_photo_metadata(tmp_path) or {}
        form.latitude.data = meta.get("latitude")
        form.longitude.data = meta.get("longitude")
        form.taken_at.data = meta.get("timestamp")
        form.address.data = get_address_from_coords(
            meta.get("latitude"),
            meta.get("longitude")
        )

        return render_template("main/upload.html",
                               title="Загрузка фото",
                               form=form,
                               preview=preview)

    if request.method == "POST" and form.submit.data and not form.file.data:
        tmp_path = session.pop("tmp_path", None)
        if not tmp_path or not os.path.exists(tmp_path):
            flash("Файл не найден, начните заново", "error")
            return redirect(url_for("upload_photo"))

        lat = form.latitude.data or None
        lon = form.longitude.data or None
        if form.address.data and (lat is None or lon is None):
            lat, lon = get_coords_from_address(form.address.data)

        with open(tmp_path, "rb") as f:
            save(
                file=f,
                user=current_user,
                latitude=lat,
                longitude=lon,
                address=form.address.data,
                timestamp=form.taken_at.data,
                description=form.description.data
            )
        os.remove(tmp_path)

        flash("Фото добавлено!", "success")
        return redirect(url_for("home"))

    return render_template("main/upload.html",
                           title="Загрузка фото",
                           form=form,
                           preview=None)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/home")
@login_required
def home():
    return render_template("main/home.html", title="Memory Keeper")


@app.route("/photos")
@login_required
def photos():
    return "gallery page"


@app.route("/photos/<filename>")
@login_required
def photo_page(filename):
    return f"photo {filename} page"


@app.route("/photos/<filename>/file")
@login_required
def get_photo(filename):
    directory = str(
        os.path.join(
            app.config["MEDIA_URL"], str(
                current_user.id)))
    return send_from_directory(directory, filename)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()
    avatar_form = AvatarForm()

    if form.submit.data:
        if form.validate_on_submit():
            form_data, user_data = form.data, current_user.__dict__

            for field in form_data.keys() & user_data.keys():
                if form_data[field] is not None:
                    if form_data[field] != user_data[field] and str(
                            form_data[field]).strip() != "":
                        setattr(current_user, field, form_data[field])
    elif avatar_form.validate_on_submit():
        encoded_image = base64.b64encode(
            avatar_form.avatar.data.read()).decode("ascii")
        current_user.avatar = encoded_image

    db = db_session.create_session()
    db.merge(current_user)
    db.commit()
    files = db.query(Photo.filename).filter(
        Photo.user_id == current_user.id).all()
    images = [[str(file[0]), "{}_tmb{}".format(
        *os.path.splitext(str(file[0])))] for file in files[::-1]]
    days = (dt.datetime.now().date() - current_user.date_of_registration).days
    statistics = {
        "k": len(files),
        "used_space": human_read_format(current_user.used_space),
        "date": ru_date(current_user.date_of_registration),
        "days": get_days_message(days)
    }
    db.close()

    return render_template(
        "main/profile.html",
        title="Профиль",
        form=form,
        avatar_form=avatar_form,
        images=images,
        stat=statistics,
        m=4 * 1024 ** 3)


if __name__ == "__main__":
    app.run(debug=True)
