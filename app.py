from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, redirect
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"{self.sno} - {self.title}"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_database():
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    with app.app_context():
        db.create_all()


create_database()


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "User already exists"

        user = User(
            username=username,
            password=generate_password_hash(password),
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect("/")

        return "Invalid credentials"

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/about")
def about():
    user_count = User.query.count()
    return render_template("about.html", user_count=user_count)


@app.route("/", methods=["GET", "POST"])
@login_required
def hello_world():
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]

        todo = Todo(title=title, desc=desc, user_id=current_user.id)
        db.session.add(todo)
        db.session.commit()

        return redirect("/")

    search = request.args.get("search")

    query = Todo.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(
            Todo.title.contains(search) | Todo.desc.contains(search)
        )

    allTodo = query.all()

    return render_template("index.html", allTodo=allTodo)


@app.route("/update/<int:sno>", methods=["GET", "POST"])
@login_required
def update(sno):
    todo = Todo.query.filter_by(sno=sno, user_id=current_user.id).first()

    if todo is None:
        return redirect("/")

    if request.method == "POST":
        todo.title = request.form["title"]
        todo.desc = request.form["desc"]

        db.session.commit()
        return redirect("/")

    return render_template("update.html", todo=todo)


@app.route("/delete/<int:sno>")
@login_required
def delete(sno):
    todo = Todo.query.filter_by(sno=sno, user_id=current_user.id).first()

    if todo is not None:
        db.session.delete(todo)
        db.session.commit()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, port=8000)
