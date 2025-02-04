import os
from functools import wraps

from flask import Flask, request, redirect, url_for, session, abort
import logging
import casbin_sqlalchemy_adapter
import casbin
from flask_sqlalchemy import SQLAlchemy


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5444/test"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session management
app.config.from_object(Config)

db = SQLAlchemy()
db.init_app(app)


# Hardcoded credentials for simplicity
USERS = {
    "alice": "password123",  # Admin
    "bob": "password456",  # User
}

# Casbin enforcer
with app.app_context():
    adapter = casbin_sqlalchemy_adapter.Adapter(db.engine)
    enforcer = casbin.Enforcer('model.conf', adapter)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get("user")
        if user:
            # Casbin enforces authorization
            if enforcer.enforce(user, request.path, request.method):
                return f(*args, **kwargs)
            else:
                abort(403)  # Forbidden
        else:
            return redirect(url_for("login"))

    return decorated


@app.route("/")
def home():
    if "user" in session:
        return (f"<p>Welcome, {session['user']}! <a href='/logout'>Logout</a></p>"
                f"<p><a href='/admin'>admin</a></p>"
                f"<p><a href='/dashboard'>dashboard</a></p>")
    return "<p>You are not logged in. <a href='/login'>Login</a></p>"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in USERS and USERS[username] == password:
            session["user"] = username
            return redirect(url_for("home"))

        return "<p>Invalid credentials. Try again.</p>"

    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


@app.route("/admin")
@requires_auth
def admin():
    return "<p>Welcome to the admin panel.</p>"


@app.route("/dashboard")
@requires_auth
def dashboard():
    return "<p>Welcome to the user dashboard.</p>"


@app.route("/reload", methods=["POST"])
def reload():
    try:
        enforcer.load_policy()
    except Exception as e:
        return {"success": False}, 400
    return {"success": True}, 200


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    app.run(debug=True)
