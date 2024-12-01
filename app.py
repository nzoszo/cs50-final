import os
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import string
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
    room = request.form.get("room")
    playerOneScore = int(request.form.get("playerOneScore"))
    playerTwoScore = int(request.form.get("playerTwoScore"))
    role = int(request.form.get("role"))
    opponent = "Player 2" if role == 1 else "Player 1"

    # Removes game room
    game_rooms.pop(room, "Room does not exist")
    
    # In case scores aren't transmitted
    if playerOneScore is None or playerTwoScore is None:
        return "Error: Missing score data", 400

    difference = abs(playerOneScore - playerTwoScore)

    return render_template("36end.html", difference=difference, playerOneScore=playerOneScore, playerTwoScore=playerTwoScore, role=role, opponent=opponent)

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

# Dictionary to store game rooms
game_rooms = {}

@app.route("/create_room")
@login_required
def create_room():
    # Generate a random 6-character room code
    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Initialize the room in the game_rooms dictionary
    game_rooms[room_code] = {
        'players': [],      # List to store player session IDs
        'roles': {},        # Maps session IDs to player1 or player2 
        'game_state': None  # Will store the game state once the game starts
    }
    
    # Render the room template, passing the room code
    return render_template("room.html", room_code=room_code)

@app.route("/join_room/<room_code>")
@login_required
def join_room_route(room_code):
    # Check if the room exists
    if room_code in game_rooms:
        # If it does, render the room template
        return render_template("room.html", room_code=room_code)
    else:
        # If it doesn't, return a 404 error
        return "Room not found", 404

@socketio.on('join_room')
def on_join(data):
    # Gets the room code
    room = data['room']
    print(f"I AM {room}")

    # Check if the room exists and has less than 2 players
    if room in game_rooms and len(game_rooms[room]['players']) < 2:
        # Add the player to the room
        join_room(room)
        # Add the player's session ID to the room's player list
        game_rooms[room]['players'].append(request.sid)
        
        # Assign role based on join order
        if len(game_rooms[room]['players']) == 1:
            game_rooms[room]['roles'][request.sid] = 1
        elif len(game_rooms[room]['players']) == 2:
            game_rooms[room]['roles'][request.sid] = 2

        print(f"Player {game_rooms[room]['roles'][request.sid]} joined room {room}")

        # Emit an update to all players in the room with the number of players in the room
        emit('room_update', {'players': len(game_rooms[room]['players'])}, room=room)
        # If the room now has 2 players, start the game
        if len(game_rooms[room]['players']) == 2:
            # Emit the 'start_game' event to all players in the room
            emit('start_game', {
                'roles': game_rooms[room]['roles']
            }, room=room)

# Helper function to initialize game state
def initialize_game_state():
    return {
        'grid': list(range(1, 37)),
        'scores': {'player1': 0, 'player2': 0},
        'current_turn': 'player1'
    }

@socketio.on('make_selection')
def handle_selection(data):
    # Room, game selected, and dictionary of roles
    room = data.get('room')
    selection = data.get('selection')
    roles = data.get('roles')

    if selection == 'thirty_six':
        emit('redirect', {
            'room': room,
            'redirect': "/36",
            'roles': roles
            }, room=room)
    elif selection == 'speed':
        emit('redirect', {
            'room': room,
            'redirect': "/speed",
            'roles': roles
            }, room=room)

@socketio.on('start_game')
def start_game(data):
    # Gets room
    room = data.get('room')

    # Initializes game state
    game_rooms[room]['game_state'] = {
        'grid': list(range(1, 37)),
        'scores': {1: 0, 2: 0},
        'current_turn': 1
    }
    print(f"start game wit room: {room} and gameState: {game_rooms[room]['game_state']}")

    emit("load_game", {
        "room": room,
        "gameState": game_rooms[room]['game_state']
    }, broadcast=True)

@socketio.on('update_game_state')
def update_game_state(game_state):
    room = game_state.get("room")
    print(f"I am updated room: {room}")
    emit('game_state_updated', game_state, broadcast=True)
    

@socketio.on('disconnect')
def handle_thirtysix_disconnect():
    print('Client disconnected')

# host = os.getenv("FLASK_HOST", "127.0.0.1")  # Default to localhost

# Makes sure the app only runs when it is run directly (e.g. on my local device)
if __name__ == "__main__":
    socketio.run(app, debug=True)

