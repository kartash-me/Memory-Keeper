import base64
import datetime as dt
import os

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
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
    AccountForm,
    EmailStepForm,
    FinalStepForm,
    LoginForm,
    PhoneStepForm,
    UploadPhotoForm,
)
from functions import (
    dotenv,
    extract_photo_metadata,
    get_address_from_coords,
    get_avatar,
    get_coords_from_address,
    get_days_message,
    human_read_format,
    make_preview,
    normalize_filename,
    ru_date,
    thumbnail,
)
from mega_validators import detect_login_type, normalize_phone


app = Flask(__name__)

app.config["DEBUG"] = dotenv("DEBUG").lower() in ["true", "t", "yes", "y"]
app.config["MEDIA_URL"] = "media"
app.config["SECRET_KEY"] = dotenv("SECRET_KEY")
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024**2
app.config["ALLOWED_EXTENSIONS"] = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".bmp",
    ".ico",
]

app.jinja_env.globals["static"] = static = lambda filename: url_for(
    "static", filename=filename
)
app.jinja_env.globals["media"] = media = lambda filename: url_for(
    "get_photo", filename=filename
)
app.jinja_env.globals["photo"] = photo = lambda filename: url_for(
    "photo_page", filename=filename
)
app.jinja_env.globals["avatar"] = get_avatar

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init()


def save(
    file,
    user,
    original_filename="unknown.jpg",
    latitude=None,
    longitude=None,
    address=None,
    timestamp=None,
    description=None,
):
    directory = os.path.join(app.config["MEDIA_URL"], str(user.id))
    os.makedirs(directory, exist_ok=True)
    base_name_for_save, ext_for_save = os.path.splitext(original_filename)

    if not base_name_for_save.strip():
        base_name_for_save = (
            f"uploaded_file_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

    if ext_for_save not in app.config["ALLOWED_EXTENSIONS"]:
        raise ValueError("Такой файл не поддерживается")

    filename = f"{base_name_for_save}{ext_for_save}"
    path = os.path.join(directory, filename)
    n = 0

    while os.path.exists(path):
        filename = f"{base_name_for_save}_{n}{ext_for_save}"
        path = os.path.join(directory, filename)
        n += 1

    with open(path, "wb") as dst:
        dst.write(file.read())

    tmb_path = thumbnail(path)

    with db_session.create_session() as db:
        photo_ = Photo(
            filename=filename,
            user_id=user.id,
            latitude=latitude,
            longitude=longitude,
            address=address,
            timestamp=timestamp,
            description=description,
        )
        size = os.path.getsize(path) + os.path.getsize(tmb_path)
        user.used_space += size
        db.merge(user)
        db.add(photo_)
        db.commit()


@login_manager.user_loader
def load_user(user_id):
    with db_session.create_session() as db:
        return db.get(User, int(user_id))


@app.context_processor
def inject_active_page():
    return {"active_page": request.endpoint}


@app.route("/")
def home():
    return render_template("promotion/home.html", title="Memory Keeper")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("gallery"))

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
                return redirect(url_for("gallery"))

            flash("Неверные данные для входа", "error")

    return render_template("promotion/form.html", title="Авторизация", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("gallery"))

    step = session.get("step", 0)
    forms = [PhoneStepForm(), EmailStepForm(), FinalStepForm()]
    form = forms[step]

    if form.validate_on_submit():
        if step == 0:
            session["number"] = normalize_phone(form.number.data)
            session["step"] = 1
            return redirect(url_for("register"))

        if step == 1:
            session["email"] = form.email.data
            session["step"] = 2
            return redirect(url_for("register"))

        if step == 2:
            with db_session.create_session() as db:
                user = User(
                    number=session["number"],
                    email=session["email"],
                    login=form.login.data,
                    date_of_registration=dt.datetime.now(),
                )
                user.set_password(form.password.data)
                db.add(user)
                db.commit()
                session.clear()
                login_user(user)
                return redirect(url_for("gallery"))

    return render_template("promotion/form.html", title="Регистрация", form=form)


@app.route("/geodata")
@login_required
def geodata():
    with db_session.create_session() as db:
        photos = (
            db.query(Photo)
            .filter(
                Photo.user_id == current_user.id,
                Photo.latitude.isnot(None),
                Photo.longitude.isnot(None),
            )
            .all()
        )

        data = []
        for p in photos:
            name, ext = os.path.splitext(str(p.filename))
            thumb = f"{name}_tmb{ext}"

            data.append(
                {
                    "lat": p.latitude,
                    "lon": p.longitude,
                    "thumb": media(thumb),
                    "full": media(p.filename),
                    "address": p.address,
                    "timestamp": p.timestamp.isoformat() if p.timestamp else None,
                    "description": p.description or "",
                }
            )

    return jsonify(data)


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    form = UploadPhotoForm()

    if request.method == "POST" and form.file.data:
        file = form.file.data
        original_filename = secure_filename(normalize_filename(file.filename))

        preview = make_preview(file)

        user_media_dir = os.path.join(app.config["MEDIA_URL"], str(current_user.id))
        tmp_dir = os.path.join(user_media_dir, "tmp")

        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.join(
            tmp_dir, "temp_upload" + os.path.splitext(original_filename)[1]
        )
        file.seek(0)
        file.save(tmp_path)
        session["tmp_path"] = tmp_path
        session["original_filename"] = original_filename

        # EXIF-мета
        meta = extract_photo_metadata(tmp_path) or {}
        form.latitude.data = meta.get("latitude")
        form.longitude.data = meta.get("longitude")
        form.taken_at.data = meta.get("timestamp")
        form.address.data = get_address_from_coords(
            meta.get("latitude"), meta.get("longitude")
        )

        return render_template(
            "main/upload.html", title="Загрузка фото", form=form, preview=preview
        )

    if request.method == "POST" and form.submit.data and not form.file.data:
        tmp_path = session.pop("tmp_path", "")
        original_filename = session.pop("original_filename", "uploaded.jpg")

        if tmp_path == "" or not os.path.exists(tmp_path):
            flash("Файл не найден, попробуйте снова", "error")
            return redirect(url_for("upload"))

        lat = form.latitude.data or None
        lon = form.longitude.data or None

        if form.address.data and (lat is None or lon is None):
            lat, lon = get_coords_from_address(form.address.data)

        with open(tmp_path, "rb") as f:
            save(
                file=f,
                user=current_user,
                original_filename=original_filename,
                latitude=lat,
                longitude=lon,
                address=form.address.data,
                timestamp=form.taken_at.data,
                description=form.description.data,
            )
        os.remove(tmp_path)

        flash("Фото добавлено!", "success")
        return redirect(url_for("gallery"))

    return render_template(
        "main/upload.html", title="Загрузка фото", form=form, preview=None
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/gallery")
@login_required
def gallery():
    return render_template("main/gallery.html", title="Галерея")


@app.route("/gallery/<filename>")
@login_required
def photo_page(filename):
    return f"photo {filename} page"


@app.route("/gallery/<filename>/file")
@login_required
def get_photo(filename):
    directory = str(os.path.join(app.config["MEDIA_URL"], str(current_user.id)))
    return send_from_directory(directory, filename)


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = AccountForm()
    avatar_form = AvatarForm()

    if form.submit.data:
        if form.validate_on_submit():
            form_data, user_data = form.data, current_user.__dict__

            for field in form_data.keys() & user_data.keys():
                if form_data[field] is not None:
                    if (
                        form_data[field] != user_data[field]
                        and str(form_data[field]).strip() != ""
                    ):
                        setattr(current_user, field, form_data[field])
    elif avatar_form.validate_on_submit():
        encoded_image = base64.b64encode(avatar_form.avatar.data.read()).decode("ascii")
        current_user.avatar = encoded_image

    db = db_session.create_session()
    db.merge(current_user)
    db.commit()
    files = db.query(Photo.filename).filter(Photo.user_id == current_user.id).all()
    images = [
        [str(file[0]), "{}_tmb{}".format(*os.path.splitext(str(file[0])))]
        for file in files[::-1]
    ]
    days = (dt.datetime.now().date() - current_user.date_of_registration).days
    statistics = {
        "photos": len(files),
        "used_space": human_read_format(current_user.used_space),
        "date": ru_date(current_user.date_of_registration),
        "days": get_days_message(days),
    }
    db.close()
    max_space = 4 * 1024**3

    return render_template(
        "main/account.html",
        title="Аккаунт",
        form=form,
        avatar_form=avatar_form,
        images=images[:7],
        statistics=statistics,
        max_space=max_space,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=app.config["DEBUG"])
