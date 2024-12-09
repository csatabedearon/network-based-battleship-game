import json
import os
import random
import socket
import threading
import time

import colorama
from colorama import Back, Fore, Style

# Initialize colorama for colored terminal output
colorama.init(autoreset=True)

HOST = "localhost"
PORT = 5555

# Queue to hold waiting players
waiting_players = []
queue_condition = threading.Condition()

# Lists to track connected players and active matches
connected_players = []
active_matches = []

# Locks for updating connected players and matches safely in multithreading
players_lock = threading.Lock()
matches_lock = threading.Lock()

# Board settings
BOARD_SIZE = 10
SHIP_SIZES = [5, 4, 3, 3, 2]  # Classic Battleship ship sizes


class Player:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address
        self.paired_event = (
            threading.Event()
        )  # Event to signal when the player has been paired
        self.game_thread = None  # To store the game thread reference
        self.username = (
            f"{address[0]}:{address[1]}"  # Default username based on address
        )
        self.opponent = None  # Reference to the opponent player


def send_message(sock, message_dict):
    try:
        # Encode the message dict as JSON
        message = json.dumps(message_dict).encode()
        # Get the length of the message
        message_length = len(message)
        # Pack the length into 4 bytes
        sock.sendall(message_length.to_bytes(4, byteorder="big") + message)
    except Exception as e:
        print(Fore.RED + f"Error sending message: {e}")


def receive_message(sock):
    # Read the message length (first 4 bytes)
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    # Unpack message length as big-endian integer
    msglen = int.from_bytes(raw_msglen, byteorder="big")
    # Read the message data
    return recvall(sock, msglen)


def recvall(sock, n):
    # Helper function to receive n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        try:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        except Exception:
            return None
    return data


def create_board():
    # Create a new game board initialized with water '~'
    return [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def place_ships(board):
    # Randomly place ships on the board for a single player
    for ship_size in SHIP_SIZES:
        placed = False
        while not placed:
            orientation = random.choice(["H", "V"])  # Choose random orientation
            row = random.randint(0, BOARD_SIZE - 1)
            col = random.randint(0, BOARD_SIZE - 1)
            if can_place_ship(board, row, col, ship_size, orientation):
                # Place ship of given size at the position
                for i in range(ship_size):
                    if orientation == "H":
                        board[row][col + i] = "S"  # Mark ship part horizontally
                    else:
                        board[row + i][col] = "S"  # Mark ship part vertically
                placed = True  # Ship successfully placed


def can_place_ship(board, row, col, size, orientation):
    # Check if a ship can be placed at the given position with the given orientation
    if orientation == "H" and col + size > BOARD_SIZE:
        return False  # Ship would go off the board horizontally
    if orientation == "V" and row + size > BOARD_SIZE:
        return False  # Ship would go off the board vertically
    for i in range(size):
        r = row + i if orientation == "V" else row
        c = col + i if orientation == "H" else col
        if board[r][c] != "~":
            return False  # Position is already occupied
    return True  # Ship can be placed


def process_move(board, row, col):
    # Process a player's move and update the board
    if board[row][col] == "S":
        board[row][col] = "X"  # Hit a ship
        return "hit"
    elif board[row][col] == "~":
        board[row][col] = "O"  # Missed, mark as 'O'
        return "miss"
    else:
        # The position has already been attacked
        return "already"


def check_win(board):
    # Check if all ships have been sunk on the board
    for row in board:
        if "S" in row:
            return False  # At least one ship part remains
    return True  # All ships have been sunk


def print_boards_side_by_side(board1, board2, player1_name, player2_name):
    # Display two boards side by side for server status monitoring
    header = f"{player1_name}'s Board{' ' * 19}{player2_name}'s Board"
    print(header)
    print("-" * len(header))
    header_row = "   " + " ".join([chr(i + ord("A")) for i in range(BOARD_SIZE)])
    print(f"{header_row}   {header_row}")
    for idx in range(BOARD_SIZE):
        row1 = board1[idx]
        row2 = board2[idx]
        display_row1 = []
        for cell in row1:
            # Color code the display based on cell content
            if cell == "S":
                display_row1.append(Back.WHITE + "S" + Style.RESET_ALL)  # Ship
            elif cell == "X":
                display_row1.append(Fore.RED + "X" + Style.RESET_ALL)  # Hit
            elif cell == "O":
                display_row1.append(Fore.BLUE + "O" + Style.RESET_ALL)  # Miss
            else:
                display_row1.append("~")  # Water
        display_row2 = []
        for cell in row2:
            if cell == "S":
                display_row2.append(Back.WHITE + "S" + Style.RESET_ALL)
            elif cell == "X":
                display_row2.append(Fore.RED + "X" + Style.RESET_ALL)
            elif cell == "O":
                display_row2.append(Fore.BLUE + "O" + Style.RESET_ALL)
            else:
                display_row2.append("~")
        print(f"{idx:2} {' '.join(display_row1)}   {idx:2} {' '.join(display_row2)}")
    print()


def display_server_status():
    # Clear the console and display current server status
    os.system("cls" if os.name == "nt" else "clear")
    with players_lock:
        num_players = len(connected_players)
    with matches_lock:
        num_matches = len(active_matches)
    print(Fore.CYAN + f"Current Connected Players: {num_players}")
    print(Fore.CYAN + f"Current Active Matches: {num_matches}\n")

    print(Fore.MAGENTA + "Active Matches and Boards:")
    print(Fore.MAGENTA + "=" * 47 + "\n")

    with matches_lock:
        for idx, match in enumerate(active_matches, 1):
            player1, player2, boards = match
            print(
                Fore.YELLOW + f"Match {idx}: {player1.username} vs {player2.username}"
            )
            print_boards_side_by_side(
                boards[player1]["own_board"],
                boards[player2]["own_board"],
                player1.username,
                player2.username,
            )
            print(Fore.MAGENTA + "=" * 47)


def handle_client(player):
    # Handle client connection, receive username, and add to matchmaking queue
    print(Fore.GREEN + f"New connection from {player.address}")
    with players_lock:
        connected_players.append(player)
    # Receive username from client
    try:
        data = receive_message(player.socket)
        if data:
            message = json.loads(data.decode())
            if message.get("type") == "username":
                player.username = message["data"]["username"]
    except Exception as e:
        print(Fore.RED + f"Error receiving username: {e}")
        # Remove player and exit
        with players_lock:
            connected_players.remove(player)
        player.socket.close()
        return
    display_server_status()

    # Notify player that they are waiting in the queue
    try:
        send_message(
            player.socket,
            {
                "status": "waiting",
                "message": "You are in the queue, waiting for an opponent...",
            },
        )
    except Exception as e:
        print(Fore.RED + f"Error sending waiting message: {e}")
        with players_lock:
            connected_players.remove(player)
        player.socket.close()
        return

    with queue_condition:
        waiting_players.append(player)
        queue_condition.notify()  # Notify the matchmaking thread

    # Wait until the player is paired or disconnected
    try:
        player.paired_event.wait()
    except Exception as e:
        print(Fore.RED + f"Error during pairing: {e}")

    # The game_session will handle communication from here
    if player.game_thread:
        player.game_thread.join()  # Wait for the game session to end

    try:
        player.socket.close()
    except Exception:
        pass

    with players_lock:
        if player in connected_players:
            connected_players.remove(player)
    display_server_status()
    print(Fore.YELLOW + f"Connection closed with {player.address}")


def matchmaking_thread():
    # Matchmaking thread that pairs players when available
    while True:
        try:
            with queue_condition:
                while len(waiting_players) < 2:
                    queue_condition.wait()  # Wait until at least two players are waiting
                # Get two players from the waiting list
                player1 = waiting_players.pop(0)
                player2 = waiting_players.pop(0)
            # Check if both players are still connected
            if player1.socket.fileno() == -1:
                # Player1 socket is closed
                with queue_condition:
                    if player2 not in waiting_players:
                        waiting_players.insert(0, player2)
                continue
            if player2.socket.fileno() == -1:
                # Player2 socket is closed
                with queue_condition:
                    if player1 not in waiting_players:
                        waiting_players.insert(0, player1)
                continue
            # Start a new game session in a separate thread
            game_thread = threading.Thread(target=game_session, args=(player1, player2))
            # Store the game thread in the player objects
            player1.game_thread = game_thread
            player2.game_thread = game_thread
            game_thread.start()
        except Exception as e:
            print(Fore.RED + f"Exception in matchmaking_thread: {e}")
            # Continue the loop to keep matchmaking


def game_session(player1, player2):
    # Start a game session between two players
    try:
        # Signal that both players have been paired
        player1.paired_event.set()
        player2.paired_event.set()

        # Initialize boards for each player and place ships
        board1 = create_board()
        board2 = create_board()
        place_ships(board1)
        place_ships(board2)

        # Assign opponents
        player1.opponent = player2
        player2.opponent = player1

        # Each player's view of their own board and the opponent's board
        boards = {
            player1: {"own_board": board1, "opponent_board": create_board()},
            player2: {"own_board": board2, "opponent_board": create_board()},
        }

        # Add match to active matches list
        with matches_lock:
            active_matches.append((player1, player2, boards))
        display_server_status()

        # Send initial messages to both players
        start_message = {
            "status": "paired",
            "message": "You have been paired with an opponent. Game starting!",
        }
        send_message(player1.socket, start_message)
        send_message(player2.socket, start_message)

        # Send initial boards to both players
        send_message(
            player1.socket,
            {
                "type": "update",
                "data": {
                    "own_board": boards[player1]["own_board"],
                    "opponent_board": boards[player1]["opponent_board"],
                    "message": "Game started. Here are your boards.",
                },
            },
        )
        send_message(
            player2.socket,
            {
                "type": "update",
                "data": {
                    "own_board": boards[player2]["own_board"],
                    "opponent_board": boards[player2]["opponent_board"],
                    "message": "Game started. Here are your boards.",
                },
            },
        )

        # Assign player turns
        current_player = player1
        opponent = player2

        # Game loop
        while True:
            try:
                # Notify current player it's their turn
                send_message(
                    current_player.socket,
                    {"status": "your_turn", "message": "It's your turn."},
                )

                # Receive move from current player
                move_data = receive_message(current_player.socket)
                if not move_data:
                    print(
                        Fore.RED
                        + f"Connection lost with {current_player.username}. Ending game."
                    )
                    break
                move = json.loads(move_data.decode())

                if move.get("type") != "move":
                    # Invalid message type
                    send_message(
                        current_player.socket,
                        {"status": "error", "message": "Invalid message type."},
                    )
                    continue

                row = move["data"]["row"]
                col = move["data"]["col"]

                # Validate move coordinates
                if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
                    send_message(
                        current_player.socket,
                        {"status": "error", "message": "Invalid move coordinates."},
                    )
                    continue

                # Process move on opponent's board
                result = process_move(boards[opponent]["own_board"], row, col)

                # Update opponent's board as seen by the current player
                if result == "hit":
                    boards[current_player]["opponent_board"][row][col] = "X"
                    message = "You hit a ship!"
                elif result == "miss":
                    boards[current_player]["opponent_board"][row][col] = "O"
                    message = "You missed."
                elif result == "already":
                    message = "You already attacked that position."
                    send_message(
                        current_player.socket,
                        {"status": "message", "message": message},
                    )
                    continue  # Let the player try again

                # Send update to current player
                send_message(
                    current_player.socket,
                    {
                        "type": "update",
                        "data": {
                            "own_board": boards[current_player]["own_board"],
                            "opponent_board": boards[current_player]["opponent_board"],
                            "message": message,
                        },
                    },
                )

                # Notify opponent and send updated own board
                opponent_message = (
                    f"The opponent attacked ({row}, {col}) and it was a {result}."
                )
                send_message(
                    opponent.socket,
                    {
                        "type": "update",
                        "data": {
                            "own_board": boards[opponent]["own_board"],
                            "opponent_board": boards[opponent]["opponent_board"],
                            "message": opponent_message,
                        },
                    },
                )

                display_server_status()  # Update server display after each move

                # Check for win condition
                if check_win(boards[opponent]["own_board"]):
                    # Current player wins
                    send_message(
                        current_player.socket,
                        {"type": "result", "data": {"winner": "You win!"}},
                    )
                    send_message(
                        opponent.socket,
                        {"type": "result", "data": {"winner": "You lose."}},
                    )
                    break  # End game loop

                # Swap turns
                current_player, opponent = opponent, current_player

            except Exception as e:
                print(Fore.RED + f"An error occurred during game: {e}")
                break

    finally:
        # Remove match from active matches list
        with matches_lock:
            active_matches[:] = [
                m for m in active_matches if m[0] != player1 and m[1] != player2
            ]
        display_server_status()

        # Close connections for both players
        try:
            player1.socket.close()
        except Exception:
            pass
        try:
            player2.socket.close()
        except Exception:
            pass


# Main server function to accept connections and start threads
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print(Fore.CYAN + f"Server listening on {HOST}:{PORT}")
# Start the matchmaking thread
threading.Thread(target=matchmaking_thread, daemon=True).start()
while True:
    try:
        # Accept new client connections
        client_socket, address = server.accept()
        print(f"Accepted connection from {address}")
        player = Player(client_socket, address)
        # Start a new thread to handle the client
        threading.Thread(target=handle_client, args=(player,), daemon=True).start()
    except Exception as e:
        print(Fore.RED + f"Error accepting connections: {e}")
        break
