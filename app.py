from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///36.db")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    return render_template("index.html")

@app.route("/36", methods=["GET", "POST"])
@login_required
def thirty_six():
    return render_template("36.html")

@app.route("/36end", methods=["POST"])
@login_required
def thirty_six_end():
    """ Decides winner and returns scores """
    playerOneScore = request.form.get("playerOneScore")
    playerTwoScore = request.form.get("playerTwoScore")

    difference = int(playerTwoScore) - int(playerOneScore)
    winner = "Player Two"

    if int(playerOneScore) > int(playerTwoScore):
        winner = "Player One"
        difference = int(playerOneScore) - int(playerTwoScore)

    return render_template("36end.html", difference=difference, playerOneScore=playerOneScore, playerTwoScore=playerTwoScore, winner=winner)

@app.route("/speed", methods=["GET", "POST"])
@login_required
def speed():
    return render_template("speed.html")

@app.route("/layout")
def layout():
    return render_template("layout.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")
        # Checks if username is inputted
        if not username:
            return apology("must input username")
        # Checks if password is inputted
        elif not password:
            return apology("must input password")
        # Checks if password is confirmed
        elif not confirm:
            return apology("must confirm password")
        # Checks if password equals confirmation
        elif password != confirm:
            return apology("passwords do not match")
        # Checks if username already exists and registers new users
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                   username, generate_password_hash(password, method='pbkdf2:sha1', salt_length=8))
        except:
            return apology("username already exists")
        # Logs in user
        session["user_id"] = db.execute("SELECT id FROM users WHERE username = (?)", username)[0]['id']
        return redirect("/")

    return render_template("register.html")
