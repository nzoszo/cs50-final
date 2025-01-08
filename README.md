# 36 
## Prelude
### Video Demo: [CS50 Final Project Video](https://youtu.be/h0todceIE-4)
### Description:
36 is a free online multiplayer game that challenges players in a strategic duel of critical thinking and math skills.

It consists of two players taking turns at removing numbers from a 6x6 grid listed from 1-36. When a player clicks a number, it is permanently removed from the grid and its value is added to his or her score. The catch, though, is that all the factors of the number clicked are also permanently removed from the grid and added to the opponent’s score.

For example, if a player clicks the number 15, it is permanently removed from the grid, and 15 gets added to his or her score. Its factors of 1, 3, and 5, however, are also permanently removed from the grid and are added to the opponent’s score.

But if a factor is removed from the grid, it can no longer be used as any points for an opponent.

To continue the example, if a player then clicks 30, none of its factors of 1, 3, 5, and 15 can be included in the opponent’s score.

Once all numbers are removed from the grid, the game ends, and the player with the higher score is declared victorious and (essentially) smarter! Can you solve a winning approach?
### Can Ignore
Developed whole other game. Based on the card game "speed," in which players race to deplete all of their cards.

Ran out of time to fully implement online mode, given code offers full functionality otherwise for one player.

As a a result of its incompleteness, ignore files:

[card_images](./static/card_images/)  -- Stored card front/backside images

[speed_styling](./static/styles.css)  -- All the styling under "/* Speed */"

[speed.html](./templates/speed.html)  -- Speed html file

## Deep Dive into Files
### Backend (Flask)
[app.py](./app.py) utilizes both Flask and SocketIO.

A few of the routes are identical to that of the Week 9's Finance Problem Set, specifically the register, login, and out logout  (**NOTE: These are not employed in final product, nor is the navbar in layout.html**)
#### /
The homepage greets users with the option to create a room or join one by inputting a code. To create one, the user simply clicks "Play!" without inputting a join code, and to join a room, the user inputs the join code then clicks "Play!" It additionally displays an instructional "How To Play" message below this container (keen eyes will notice it's "similar" to the one outlined in the beginning of this markup).
### Room Management
When a user is directed to the [/create_room](./templates/room.html) route, a 6 string code of uppercased, random characters is generated and associated with that current room. A dictionary of all game rooms (game_rooms) appends this room as an index, with each index (room) consisting of the room's players, roles (i.e. who is player 1 or player 2), and the game state (a list from 1-36).

When a user joins a room, he or she is directed to the [/join_room/<room_code>](./templates/room.html) route, where the <room_code> is the code he or she inputs in the homepage's "Join Code" textfield. A quick query checks if the room exists in game_rooms, and if so, the user is redirected to that room with the player who created it. If not, a 404 error is returned.
### Bi-Directional Communication (SocketIO)
In the above examples, where a user either creates a new or joins an existing room, the user is directed to the interface of [room.html](./templates/room.html). 

This user is a client, and [app.py](./app.py) serves as the server. And after the client's redirection to [room.html](./templates/room.html), a bi-directional SocketIO connection is established between the two. This means each one is able to communicate messages between each other in real-time.
#### First Connection ("join_room", client -> server)
The first "message" begins in [room.html](./templates/room.html) when the client connects as it "emits" the "join_room" message, and in it, the room he or she is inside, to the server. The server then receives this and immediately checks if the room is in the list of available game rooms or not (game_rooms) and if the length of its players is less than 2. If so, then it adds the client to the room and to the backend dictionary "game_rooms." It then assigns each client to either player 1 or player 2 depending on who created the game (i.e. joined first) and who joined it (i.e. joined second). Lastly it checks if the room now has 2 players, and if so, then if emits the "start_game" message to each client, with a package of data that sends over each user's role.
#### Game Begins ("game_start", server -> client)
The clients each identify their own roles. If the client is player one, then he or she will be given the option to choose the game. There are 3 options: 36, Speed!, and Word World (**NOTE: As of December 17, 2024, only 36 is completed**). Each option is given an event listener for if it was clicked, and if so, then it will wait until the play button is clicked, and at once will emit the selected option to the server in "make_selection."
#### Redirecting Clients ("make_selection" and "redirect" client -> server and server -> client, respectivelty)
The server redirects both clients accordingly to the selected game in their specific room by emitting "redirect" with the aforementioned parameters in addition to each client's role.

After each client receives this emit, they are both redirected to a url containing the correct game, each client's specific role, and the room number. **Since only 36 is completed, all proceeding information pertains to that game**
## The Game
### Initial Game State
Using for loops to create a 2D list and accessing its values with the Django Template, the 6x6 grid with numbers 1-36 is visually generated. Each number is contained in a box cell that when hovered upon is highlighted.

At the top of the screen, is turnDisplay, which maintains the current turn in real-time.

At the bottom of the screen, is each player's corresponding score in a T-Chart.
#### Dynamic Settings
Each client identifies it's role by extracting it from the passed parameters in the url. According to their role, any mention of "Player 1" or "Player 2," be it in the turnDisplay or each player's scores is color coordinated to each client. The current player's color will appear green and their opponent's red. Furthermore, a parenthesis-enclosed "You" will encompass every occurence of a role if it correctly corresponds to the client.
#### Visual Board Connects with Backend Board ("start_game" client -> server)
The game_state in the game room is initialized with grid (a list of integers from 1-36), scores (each player's score; key is denoted by player number), and current_turn. This object is then passed onto each client in the emitted "load_game." (**NOTE: It should be only broadcasted to clients in that room, but game curiously does not function when room=room in last emit parameter. As such, instead of room=room, it is broadcast=True, meaning all clients are affected. In essence, only two players can play at any time.**)
#### Game Finally Begins and Is Playable (server -> client)
Each client runs the function "initalizeGame()," with the parameters of the recently-parsed backend game_state, the room, and the current player.

In "initializeGame()," the turnDisplay is immediately updated with "updateTurnIndicator()" to correspond the colors to each client. Then the player whose turn it is is enabled to click as each number is given an event listener if it is clicked. If it is, it plays a sound and proceeds to the next segment under the function "handleClick," passing in the element just clicked, the current game state, whose turn it is, and which player clicked it.
#### Processing a Turn (handleClick())
The number is extracted from the clicked element. Its value is added to the player who clicked it in the game state, and it is also removed from the backend grid in gameState. 

The available factors of that number are then generated in a list by checking each number in the backend grid to see if the number is cleanly divisible with it.

Each factor is then looped through to add to the score of the opponent in the backend game state, and it is also removed from the backend grid.

The turn then changes to the other player in both the backend and frontend, and the information of the game state, the nubmer clicked, and the factors of those numbers are emitted to the server in "update_game_state."

The server then sends back the data immediately without change. This back and forth exchange of the same data ensures both clients are refreshed with the same data in real-time. (**NOTE: Again, same with the earlier emit of "load_game," the game would only work if broadcast were set to True**).
### Game Logic
When the updated game state is sent to both clients, each client the turnDisplay, which player can make a move, scores, and the visual grid/board. It does so with the following functions: updateTurnIndicator(), enablePlayerTurn(), displayScore(), and displayBoard(), in respect to the order outlined earlier. The former two have already been discussed previously.
#### displayScore()
It has only one accepted parameter which is the updated game state.

Updates each players' score visually by accessing the values from the updated backend grid.
#### displayBoard()
Its accepted parameters are the updated game state, the number that was clicked and its factors.

It then matches the number clicked to its element in the grid.
#### Animation
A new span element is created and positioned above and to the right of the element clicked. It is given the class "factor-animation" and an innerHTML of the concatenation of "+" and the number that was clicked (e.g +7, if the number 7 was clicked). The color of the span is adjusted according to each client: green to the user who clicked because that's a number being added to his or her score, and red to the opponent for added bonus. The element clicked is then removed from the grid and appends the described animation as a child for it to occur.

Enumerates all the elements of the factors of the clicked number as a list. Then loops through that list to perform identical operation to factors. Animation is produced, but colors are reversed: green to the opponent of the player who clicked it because he or she is getting that value added to his or her score. Factor is also removed from the frontend grid and span animation element appended to factor element.

And to make sure only the available factors and numbers clicked display the span animation, all elements with the animation (in the form of the class "factor-animation") are removed of this class at the beginning of the function.

Lastly checks if there are no more any numbers on the grid, and if so, then an object is constructed with the following data: the scores of each player, the role of the client, and the room. This data is then sent as a form to [36end.html](./templates/36end.html) to which each client is also redirected.
### End Screen
[app.py](./app.py): The server parses the form data, accessing the room, each players' score, the client's role, and the opponent of the client. The room is then removed from the dictionary of game rooms. The html of the end screen is then rendered with the following data: the positive difference of the two players' scores, each players' score, and each clients' role and opponent.

[36end.html](./templates/36end.html): The frontend for each client dynamically displays the results, showcasing victory for the winner and defeat for the loser alongside the scores of each player. Each player and his or her opponent for each client is also dynamically colored according to the previous green and red and ties are also accounted for. Lastly there is a button for a new game that redirects the client to the homepage.
## Future Plans
* Connect to Real Online Hosting
* Be open to more than 2 players at a time --- fixing the broadcast issue
* Put together the draft card game "Speed" with SocketIO connection for effective online multiplayer
* Create word-based game to fit "World of Words"