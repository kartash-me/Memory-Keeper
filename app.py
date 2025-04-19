from flask import Flask
from data import db_session


app = Flask(__name__)


@app.route("/")
def index():
    return "main application page"


def db_set():
    db_session.global_init("db/memory_keeper.db")


if __name__ == "__main__":
    db_set()
    app.run()
