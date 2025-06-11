# Network-Based Battleship Game

A classic game of Battleship playable over a local network. This project features a client-server architecture where a central server manages matchmaking and game state, allowing two clients to connect and play against each other in a turn-based battle.

## Features

- **Client-Server Architecture**: A robust server handles multiple game sessions and player connections.
- **Automatic Matchmaking**: Players who connect are placed in a queue and automatically paired when an opponent is available.
- **Randomized Ship Placement**: Ship positions are randomized for every new game, ensuring high replayability.
- **Turn-Based Gameplay**: The server manages turns, prompting the active player for their move.
- **Interactive Terminal UI**: Colored output provides a clear and intuitive display of your board and your opponent's board (hits, misses, ships).
- **Live Server Dashboard**: The server console provides a real-time overview of connected players, active matches, and the current state of all game boards.

## Project Structure

```
network-based-battleship-game/
├── .gitignore          # Files for Git to ignore
├── README.md           # You are here!
├── requirements.txt    # Project dependencies
├── run_2_clients.bat   # Script to start two clients (server must be running)
├── run_game.bat        # Script to start the server and two clients
└── src/
    ├── __init__.py     # Makes 'src' a Python package
    ├── client.py       # The game client logic
    ├── config.py       # Shared configuration (host, port, etc.)
    └── server.py       # The game server logic
```

## Prerequisites

- Python 3.7 or newer
- `pip` (Python's package installer)

## Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/csatabedearon/network-based-battleship-game.git
    ```

2.  **Navigate to the project directory:**
    ```sh
    cd network-based-battleship-game
    ```

3.  **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

## How to Run

This project is designed to be run on a local machine.

### Option 1: All-in-One (Recommended)

The easiest way to start a game is to use the provided batch script.

-   On Windows, simply double-click `run_game.bat`.

This will open three new terminal windows: one for the server and two for the clients.

### Option 2: Manual Start

If you prefer to run the components separately or are not on Windows, follow these steps.

1.  **Start the Server:**
    Open a terminal in the project's root directory and run:
    ```sh
    python -m src.server
    ```
    The server is now running and waiting for players to connect.

2.  **Start the Clients:**
    For each player, open a **new terminal** in the project's root directory and run:
    ```sh
    python -m src.client
    ```
    You can also use the `run_2_clients.bat` script on Windows to quickly open two clients if the server is already running.

## Gameplay

1.  When a client starts, you will be prompted to enter a username.
2.  You will be placed in a queue until another player connects.
3.  Once two players are in the queue, a game starts automatically.
4.  Your board (with your ships marked 'S') and an empty opponent's board will be displayed.
5.  When it's your turn, enter coordinates to fire at (e.g., `A5`, `C0`, `J9`).
6.  The game ends when one player has sunk all of the opponent's ships. `X` marks a hit, and `O` marks a miss.