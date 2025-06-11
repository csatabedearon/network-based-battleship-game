# backend/game_logic.py

import random
from config import BOARD_SIZE, SHIP_SIZES

def create_board():
    """Creates a new game board initialized with water '~'."""
    return [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def can_place_ship(board, row, col, size, orientation):
    """Checks if a ship can be placed at the given position."""
    if orientation == "H" and col + size > BOARD_SIZE:
        return False
    if orientation == "V" and row + size > BOARD_SIZE:
        return False
        
    for i in range(size):
        r, c = (row + i, col) if orientation == "V" else (row, col + i)
        if board[r][c] != "~":
            return False
    return True

def place_ships(board):
    """Randomly places ships on the board for a single player."""
    for ship_size in SHIP_SIZES:
        placed = False
        while not placed:
            orientation = random.choice(["H", "V"])
            row = random.randint(0, BOARD_SIZE - 1)
            col = random.randint(0, BOARD_SIZE - 1)
            
            if can_place_ship(board, row, col, ship_size, orientation):
                for i in range(ship_size):
                    if orientation == "H":
                        board[row][col + i] = "S"
                    else:
                        board[row + i][col] = "S"
                placed = True
    return board

def process_move(board, row, col):
    """
    Processes a player's move and updates the board.
    Returns a tuple: (result_code, message)
    result_code can be 'hit', 'miss', or 'already_tried'
    """
    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        return "invalid", "Move is out of bounds."

    if board[row][col] == "S":
        board[row][col] = "X"  # Hit
        return "hit", "It was a HIT!"
    elif board[row][col] == "~":
        board[row][col] = "O"  # Miss
        return "miss", "It was a MISS."
    elif board[row][col] in ["X", "O"]:
        return "already_tried", "You have already attacked this position."
    
    return "invalid", "Invalid move."


def check_win(board):
    """Checks if all ships have been sunk on the board."""
    for row in board:
        if "S" in row:
            return False  # At least one ship part remains
    return True