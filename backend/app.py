# backend/app.py

import uuid
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

from game_logic import create_board, place_ships, process_move, check_win

# --- APPLICATION SETUP ---
app = Flask(__name__)
# CORS is needed to allow the React frontend (running on a different port) to communicate with the backend
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# --- DATA STRUCTURES ---
# These are in-memory data stores. For a real production app, you might use a database like Redis.
players = {}  # Maps player SID to their username. e.g., {'sid123': 'Alice'}
waiting_queue = []  # A list of SIDs for players waiting for a game.
game_rooms = {}  # Maps a room_id to a complete game state object.

# --- SOCKET.IO EVENT HANDLERS ---

@socketio.on('connect')
def handle_connect():
    """A new client has connected to the server."""
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """A client has disconnected."""
    print(f"Client disconnected: {request.sid}")
    sid = request.sid

    # Clean up if the player was in the waiting queue
    if sid in waiting_queue:
        waiting_queue.remove(sid)
    
    # Clean up if the player was in a game
    room_to_cleanup = None
    for room_id, game in game_rooms.items():
        if sid in game['players']:
            opponent_sid = next((p for p in game['players'] if p != sid), None)
            if opponent_sid:
                # Notify the opponent that the other player has left
                emit('opponent_disconnected', {'message': f"{players.get(sid, 'Opponent')} has left the game."}, room=opponent_sid)
            room_to_cleanup = room_id
            break
    
    if room_to_cleanup:
        del game_rooms[room_to_cleanup]

    # Remove player from our registry
    if sid in players:
        del players[sid]

@socketio.on('find_game')
def handle_find_game(data):
    """Player wants to find a game. Add them to the queue."""
    sid = request.sid
    players[sid] = data.get('username', 'Anonymous')
    print(f"Player {players[sid]} ({sid}) is looking for a game.")

    if sid not in waiting_queue:
        waiting_queue.append(sid)

    emit('finding_game', {'message': 'Waiting for an opponent...'})

    # If there are enough players, start a new game
    if len(waiting_queue) >= 2:
        player1_sid = waiting_queue.pop(0)
        player2_sid = waiting_queue.pop(0)
        
        # Create a unique room for this game
        room_id = str(uuid.uuid4())
        
        # Both players join the Socket.IO room
        join_room(room_id, sid=player1_sid)
        join_room(room_id, sid=player2_sid)

        # Create the initial game state
        player1_board = place_ships(create_board())
        player2_board = place_ships(create_board())
        
        game_rooms[room_id] = {
            'players': [player1_sid, player2_sid],
            'player_names': {player1_sid: players[player1_sid], player2_sid: players[player2_sid]},
            'boards': {player1_sid: player1_board, player2_sid: player2_board},
            'opponent_views': {
                player1_sid: create_board(), # Player 1's view of Player 2's board
                player2_sid: create_board()  # Player 2's view of Player 1's board
            },
            'current_turn': player1_sid,
            'winner': None
        }

        print(f"Game starting in room {room_id} between {players[player1_sid]} and {players[player2_sid]}")

        # Notify both players that the game has started
        emit('game_started', {
            'room_id': room_id,
            'opponent_name': players[player2_sid],
            'my_board': game_rooms[room_id]['boards'][player1_sid],
            'opponent_view_board': game_rooms[room_id]['opponent_views'][player1_sid],
            'is_my_turn': True
        }, room=player1_sid)
        
        emit('game_started', {
            'room_id': room_id,
            'opponent_name': players[player1_sid],
            'my_board': game_rooms[room_id]['boards'][player2_sid],
            'opponent_view_board': game_rooms[room_id]['opponent_views'][player2_sid],
            'is_my_turn': False
        }, room=player2_sid)

@socketio.on('make_move')
def handle_make_move(data):
    """A player has made a move."""
    sid = request.sid
    room_id = data['room_id']
    row, col = data['row'], data['col']

    game = game_rooms.get(room_id)
    if not game or game['current_turn'] != sid:
        # It's not this player's turn, or the game doesn't exist.
        emit('error', {'message': "It's not your turn!"}, room=sid)
        return

    opponent_sid = next(p for p in game['players'] if p != sid)
    opponent_board = game['boards'][opponent_sid]
    player_view_board = game['opponent_views'][sid]

    result_code, message = process_move(opponent_board, row, col)

    if result_code == 'already_tried':
        emit('error', {'message': message}, room=sid)
        return # Let the player try again, don't switch turns

    # Update the player's view of the opponent's board
    player_view_board[row][col] = opponent_board[row][col]
    
    # Check for a win
    if check_win(opponent_board):
        game['winner'] = sid
        emit('game_over', {
            'winner_name': players[sid],
            'my_board': game['boards'][sid],
            'opponent_board': game['boards'][opponent_sid] # Show the final state
        }, room=room_id)
        # Clean up the game room
        del game_rooms[room_id]
        return

    # Switch turns
    game['current_turn'] = opponent_sid
    
    # Send updates to both players
    # To current player
    emit('update_game_state', {
        'message': message,
        'my_board': game['boards'][sid],
        'opponent_view_board': game['opponent_views'][sid],
        'is_my_turn': False
    }, room=sid)
    
    # To opponent
    emit('update_game_state', {
        'message': f"{players[sid]} attacked ({chr(ord('A') + col)}{row}). It's now your turn!",
        'my_board': game['boards'][opponent_sid],
        'opponent_view_board': game['opponent_views'][opponent_sid],
        'is_my_turn': True
    }, room=opponent_sid)

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    print("Starting Battleship server...")
    # host='0.0.0.0' makes the server accessible from any IP address,
    # not just localhost. This is important for Docker.
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)