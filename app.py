import os
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_socketio import SocketIO, emit
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

# Configure application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

app.config["SECRET_KEY"] = app.secret_key
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize SocketIO
socketio = SocketIO(app)

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

""" Socket.IO events """

# 36 game

@socketio.on('join_room')
def join_thirtysix_room(data):
    room = data['room']
    player = session.get('player')
    join_room(room)
    emit('room_joined', {'player': player}, room=room)

@socketio.on('start_game')
def start_game(data):
    room = data['room']
    # Initialize game state for the room
    emit('init', game_state, room=room)

# Initialize the game state
game_state = {
    'grid': list(range(1, 37)),  # Create a list of numbers from 1 to 36 for the grid
    'scores': {'player1': 0, 'player2': 0},  # Set initial scores for both players to 0
    'current_turn': 'player1',  # Start with Player 1's turn
    'number_clicked': 0 # Stores the number clicked
}

@socketio.on('connect')
def handle_thirysix_connect():
    """
    This function is called when a client connects to the server.
    It assigns the player as 'player1' or 'player2' based on the current turn.
    It also emits the initial game state to all connected clients.
    """
    print('A player connected')  # Print a message to the server console

    # Check if the player is already assigned in their session
    if 'player' not in session:
        # Assign the player based on the current turn
        session['player'] = 'player1' if game_state['current_turn'] == 'player1' else 'player2'
    
    # Emit the initial game state to all connected clients (broadcast)
    emit('init', game_state, broadcast=True)

@socketio.on('number_selected')
def handle_number_selected(number):
    """
    This function handles when a player selects a number.
    It updates the game state, switches turns, and emits the updated state to all clients.
    """
    player = session['player']  # Get the current player from the session
    game_state["number_clicked"] = number; # Set the number clicked

    # Ensure that only the player whose turn it is can make a move
    if game_state['current_turn'] != player:
        return  # If it's not this player's turn, do nothing

    # Remove the selected number from the grid
    game_state['grid'].remove(number)
    # Add the selected number to the current player's score
    game_state['scores'][player] += number

    # Determine the opponent
    opponent = 'player2' if player == 'player1' else 'player1'
    
    # Find factors of the selected number that are still on the grid
    factors = [n for n in game_state['grid'] if number % n == 0]
    """
    Explanation of the line above:
    - This is a list comprehension.
    - It iterates over each number `n` in `game_state['grid']`.
    - It checks if `number % n == 0`, which means `n` is a factor of `number`.
    - If `n` is a factor, it is included in the list `factors`.
    - This list contains all the factors of the selected number that are still available on the grid.
    """

    for factor in factors:
        # Remove each factor from the grid
        game_state['grid'].remove(factor)
        # Add the factor's value to the opponent's score
        game_state['scores'][opponent] += factor

    # Switch the turn to the opponent
    game_state['current_turn'] = opponent

    # Emit the updated game state to all connected clients (broadcast)
    emit('update_state', game_state, broadcast=True)

    # Check if the game has ended (i.e., no numbers left on the grid)
    if not game_state['grid']:
        # Determine the winner based on who has the higher score
        winner = 'player1' if game_state['scores']['player1'] > game_state['scores']['player2'] else 'player2'
        # Emit the game end event with the winner's information
        emit('game_end', {'winner': winner}, broadcast=True)

@socketio.on('disconnect')
def handle_thirtysix_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_thirtysix_message(message):
    print(f'Received message: {message}')
    emit('message', message, broadcast=True)

# Makes sure the app only runs when it is run directly (e.g. on my local device)
if __name__ == "__main__":
    socketio.run(app)

