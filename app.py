from flask import Flask, render_template


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("base.html", title="Memory Keeper")


@app.route("/login")
def login():
    return "this page is currently under development"


@app.route("/register")
def register():
    return "this page is currently under development"


if __name__ == "__main__":
    app.run()
