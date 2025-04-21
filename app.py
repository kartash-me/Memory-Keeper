from flask import Flask, render_template, redirect, request, session
from data import db_session
from data.users import User
from forms import PhoneStepForm, EmailStepForm, FinalStepForm, LoginForm
from flask_login import LoginManager, login_user, logout_user, login_required


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
    return "this page is currently under development"


@app.route('/register', methods=['GET', 'POST'])
def register():
    return "this page is currently under development"


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


if __name__ == "__main__":
    app.run()
