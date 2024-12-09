import json
import socket
import threading

import colorama
from colorama import Fore, Style

# Initialize colorama for colored terminal output
colorama.init(autoreset=True)

HOST = "localhost"
PORT = 5555

BOARD_SIZE = 10


def send_message(sock, message_dict):
    try:
        # Encode the message dict as JSON
        message = json.dumps(message_dict).encode()
        # Get the length of the message
        message_length = len(message)
        # Pack the length into 4 bytes
        sock.sendall(message_length.to_bytes(4, byteorder="big") + message)
    except Exception as e:
        print(f"Error sending message: {e}")
        sock.close()


def receive_message(sock):
    # Read message length (first 4 bytes)
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    # Unpack message length as big-endian integer
    msglen = int.from_bytes(raw_msglen, byteorder="big")
    # Read the message data
    data = recvall(sock, msglen)
    if data is None:
        return None
    return data.decode()


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


def print_board(board, own=False):
    # Display the board with appropriate symbols
    print("  " + " ".join([chr(i + ord("A")) for i in range(BOARD_SIZE)]))
    for idx, row in enumerate(board):
        display_row = []
        for cell in row:
            if cell == "X":
                display_row.append(Fore.RED + "X" + Style.RESET_ALL)  # Hit
            elif cell == "O":
                display_row.append(Fore.BLUE + "O" + Style.RESET_ALL)  # Miss
            elif cell == "S":
                if own:
                    display_row.append(Fore.GREEN + "S" + Style.RESET_ALL)  # Ship
                else:
                    display_row.append("~")  # Unknown
            else:
                display_row.append("~")  # Water or unknown
        print(f"{idx:2} " + " ".join(display_row))


def receive_messages(sock):
    # Receive messages from the server
    while True:
        try:
            data = receive_message(sock)
            if data is None:
                print("Connection closed by the server.")
                break
            message = json.loads(data)
            handle_server_message(sock, message)
        except Exception as e:
            print(f"An error occurred: {e}")
            sock.close()
            break


def handle_server_message(sock, message):
    # Handle different types of messages received from the server
    if message.get("status") == "waiting":
        # Waiting in the queue
        print(Fore.YELLOW + message["message"])
    elif message.get("status") == "paired":
        # Paired with an opponent
        print(Fore.GREEN + message["message"])
    elif message.get("status") == "your_turn":
        # It's the player's turn to make a move
        print(Fore.CYAN + message["message"])
        valid_input = False
        while not valid_input:
            try:
                move_input = input("Enter your move (e.g., A5): ").strip().upper()
                if len(move_input) < 2:
                    print("Invalid input format.")
                    continue
                col_char = move_input[0]
                row_str = move_input[1:]
                if not col_char.isalpha() or not row_str.isdigit():
                    print("Invalid input format.")
                    continue
                col = ord(col_char) - ord("A")
                row = int(row_str)
                if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
                    print("Coordinates out of bounds.")
                    continue
                # Send move to server
                move = {"type": "move", "data": {"row": row, "col": col}}
                send_message(sock, move)
                valid_input = True
            except Exception as e:
                print(f"Invalid input: {e}")
    elif message.get("type") == "update":
        # Update received after making a move or after being attacked
        print(Fore.GREEN + message["data"]["message"])
        own_board = message["data"].get("own_board")
        opponent_board = message["data"].get("opponent_board")
        if own_board:
            print("Your Board:")
            print_board(own_board, own=True)
        if opponent_board:
            print("Opponent's Board:")
            print_board(opponent_board, own=False)
    elif message.get("type") == "message":
        # General message from server or opponent's move notification
        print(Fore.MAGENTA + message["message"])
    elif message.get("type") == "result":
        # Game result (win or lose)
        print(Fore.GREEN + message["data"]["winner"])
        sock.close()
        exit()
    elif message.get("status") == "error":
        # Error message from server
        print(Fore.RED + f"Error: {message['message']}")
    else:
        print("Received unknown message from server.")


# Main function to start the client
username = input("Enter your username: ").strip()
if not username:
    username = "Player"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Send username to server
username_message = {"type": "username", "data": {"username": username}}
send_message(client_socket, username_message)

# Start thread to receive messages from the server
threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
threading.Event().wait()  # Wait indefinitely without consuming CPU
