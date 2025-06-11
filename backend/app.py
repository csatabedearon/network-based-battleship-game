# backend/app.py

import uuid
import random
import string
from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

from game_logic import create_board, place_ships, process_move, check_win

# --- APPLICATION SETUP ---
app = Flask(__name__, static_folder='static', static_url_path='/')
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="https://csatabedearon.info")

# --- SERVE THE REACT APP ---
# This route will serve the 'index.html' file of our React app
@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

# This is a catch-all for any other routes, to support React Router in the future
@app.route('/<path:path>')
def serve_static(path):
    # This attempts to serve a file if it exists, otherwise serves index.html
    # This is useful for client-side routing.
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return send_from_directory(app.static_folder, 'index.html')

# --- DATA STRUCTURES ---
players = {}  # Maps player SID to their username. e.g., {'sid123': 'Alice'}
waiting_queue = []  # A list of SIDs for players in the PUBLIC matchmaking queue.
game_rooms = {}  # Maps a room_id/code to a complete game state object.

# --- HELPER FUNCTION ---
def generate_room_code(length=5):
    """Generates a simple, unique room code that is not currently in use."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if code not in game_rooms:
            return code

# --- SOCKET.IO EVENT HANDLERS ---

@socketio.on('connect')
def handle_connect():
    """A new client has connected to the server."""
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """A client has disconnected. This is a critical cleanup step."""
    sid = request.sid
    print(f"Client disconnected: {sid}")

    # Clean up if the player was in the public waiting queue
    if sid in waiting_queue:
        waiting_queue.remove(sid)
        print(f"Player {players.get(sid, sid)} removed from public queue.")
    
    # Clean up if the player was in any game (public or private)
    room_to_cleanup = None
    for room_id, game in game_rooms.items():
        if sid in game.get('players', []):
            opponent_sid = next((p for p in game['players'] if p != sid), None)
            if opponent_sid and len(game['players']) > 1:
                # Notify the opponent that the other player has left
                emit('opponent_disconnected', {'message': f"{players.get(sid, 'Opponent')} has left the game."}, room=opponent_sid)
            room_to_cleanup = room_id
            break
    
    if room_to_cleanup:
        print(f"Closing game room {room_to_cleanup} due to disconnect.")
        del game_rooms[room_to_cleanup]

    # Finally, remove player from our global registry
    if sid in players:
        del players[sid]

@socketio.on('register_player')
def handle_register_player(data):
    """Associates a username with a session ID when the user enters their name."""
    sid = request.sid
    players[sid] = data.get('username', 'Anonymous')
    print(f"Player {players[sid]} ({sid}) has registered.")
    # We can send back a confirmation if needed, but for now, we just store it.

@socketio.on('find_game')
def handle_find_game(data):
    """Player wants to find a PUBLIC game. Add them to the queue."""
    sid = request.sid
    # Ensure player is registered
    if sid not in players:
        players[sid] = data.get('username', 'Anonymous')

    print(f"Player {players[sid]} ({sid}) is looking for a public game.")

    if sid not in waiting_queue:
        waiting_queue.append(sid)

    emit('finding_game', {'message': 'Searching for an opponent...'})

    # If there are enough players, start a new game
    if len(waiting_queue) >= 2:
        player1_sid = waiting_queue.pop(0)
        player2_sid = waiting_queue.pop(0)
        
        # Public games will use a UUID for the room ID
        room_id = str(uuid.uuid4())
        
        # Start the game (using a helper function to avoid code duplication)
        start_game(player1_sid, player2_sid, room_id)

@socketio.on('cancel_find_game')
def handle_cancel_find_game():
    """Player wants to leave the public matchmaking queue."""
    sid = request.sid
    if sid in waiting_queue:
        waiting_queue.remove(sid)
        print(f"Player {players.get(sid, sid)} cancelled and left the queue.")
        # Send the player back to the main menu on the frontend
        emit('main_menu')

@socketio.on('create_private_lobby')
def handle_create_private_lobby():
    """Player wants to create a private lobby."""
    sid = request.sid
    room_code = generate_room_code()
    
    join_room(room_code, sid=sid)
    
    # Create a preliminary game object. It's just a lobby for now.
    game_rooms[room_code] = {
        'players': [sid],
        'player_names': {sid: players.get(sid, 'Anonymous')},
        'is_private': True,
    }
    
    print(f"Player {players.get(sid, sid)} created private lobby with code {room_code}")
    
    # Send the code back to the creator
    emit('private_lobby_created', {'room_code': room_code})

@socketio.on('join_private_lobby')
def handle_join_private_lobby(data):
    """A second player attempts to join a private lobby with a code."""
    sid = request.sid
    room_code = data.get('room_code', '').upper()
    
    lobby = game_rooms.get(room_code)
    
    if not lobby or not lobby.get('is_private') or len(lobby['players']) != 1:
        emit('error', {'message': 'Invalid room code or the lobby is full.'})
        return

    player1_sid = lobby['players'][0]
    player2_sid = sid
    
    # Ensure joining player is registered
    if sid not in players:
        players[sid] = data.get('username', 'Anonymous')

    # The second player joins the Socket.IO room
    join_room(room_code, sid=player2_sid)
    
    # Now that we have two players, we can start the game.
    start_game(player1_sid, player2_sid, room_code)

def start_game(player1_sid, player2_sid, room_id):
    """Helper function to initialize and start a game for two players in a room."""
    # If the room already exists (private lobby), we update it.
    # If not (public match), we create it.
    game = game_rooms.get(room_id, {})
    
    # Update/set all game properties
    game.update({
        'players': [player1_sid, player2_sid],
        'player_names': {
            player1_sid: players[player1_sid], 
            player2_sid: players[player2_sid]
        },
        'boards': {
            player1_sid: place_ships(create_board()),
            player2_sid: place_ships(create_board())
        },
        'opponent_views': {
            player1_sid: create_board(),
            player2_sid: create_board()
        },
        'current_turn': player1_sid,
        'winner': None
    })
    
    # Store the fully initialized game state
    game_rooms[room_id] = game
    
    print(f"Game starting in room {room_id} between {players[player1_sid]} and {players[player2_sid]}")

    # Notify both players that the game has started
    emit('game_started', {
        'room_id': room_id,
        'opponent_name': players[player2_sid],
        'my_board': game['boards'][player1_sid],
        'opponent_view_board': game['opponent_views'][player1_sid],
        'is_my_turn': True
    }, room=player1_sid)
    
    emit('game_started', {
        'room_id': room_id,
        'opponent_name': players[player1_sid],
        'my_board': game['boards'][player2_sid],
        'opponent_view_board': game['opponent_views'][player2_sid],
        'is_my_turn': False
    }, room=player2_sid)


# --- The 'make_move' handler remains unchanged from before ---
@socketio.on('make_move')
def handle_make_move(data):
    """A player has made a move."""
    sid = request.sid
    room_id = data['room_id']
    row, col = data['row'], data['col']

    game = game_rooms.get(room_id)
    if not game or game.get('current_turn') != sid:
        emit('error', {'message': "It's not your turn!"})
        return

    opponent_sid = next(p for p in game['players'] if p != sid)
    opponent_board = game['boards'][opponent_sid]
    player_view_board = game['opponent_views'][sid]

    result_code, message = process_move(opponent_board, row, col)

    if result_code == 'already_tried':
        emit('error', {'message': message})
        return

    player_view_board[row][col] = opponent_board[row][col]
    
    if check_win(opponent_board):
        game['winner'] = sid
        emit('game_over', {
            'winner_name': players[sid],
            'my_board': game['boards'][sid],
            'opponent_board': game['boards'][opponent_sid]
        }, room=room_id)
        # Clean up the game room after it's over
        if room_id in game_rooms:
            del game_rooms[room_id]
        return

    # Switch turns
    game['current_turn'] = opponent_sid
    
    # Send updates to both players
    emit('update_game_state', {
        'message': message,
        'my_board': game['boards'][sid],
        'opponent_view_board': game['opponent_views'][sid],
        'is_my_turn': False
    }, room=sid)
    
    emit('update_game_state', {
        'message': f"{players[sid]} attacked ({chr(ord('A') + col)}{row}). It's now your turn!",
        'my_board': game['boards'][opponent_sid],
        'opponent_view_board': game['opponent_views'][opponent_sid],
        'is_my_turn': True
    }, room=opponent_sid)


# --- MAIN EXECUTION ---
if __name__ == '__main__':
    print("Starting Battleship server...")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)