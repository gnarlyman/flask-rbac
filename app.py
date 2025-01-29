from functools import wraps

from flask import Flask, request, redirect, url_for, session, abort
from flask_authz import CasbinEnforcer
import logging

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session management

# Hardcoded credentials for simplicity
USERS = {
    "alice": "password123",  # Admin
    "bob": "password456",  # User
}

# Casbin enforcer
app.config["CASBIN_MODEL"] = "model.conf"
app.config["CASBIN_POLICY"] = "policy.csv"
app.config["CASBIN_OWNER_HEADERS"] = []
authz = CasbinEnforcer(app)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get("user")
        if user:
            # Casbin enforces authorization
            if authz.e.enforce(user, request.path, request.method):
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    app.run(debug=True)
