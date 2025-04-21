from flask import Flask, render_template

from data import db_session


app = Flask(__name__)
db_session.global_init("db/memory_keeper.db")

@app.route("/")
def index():
    return render_template("base.html")


if __name__ == "__main__":
    app.run()
