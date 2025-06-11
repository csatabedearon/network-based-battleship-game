import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import Board from './components/Board';

// Connect to the backend server.
const socket = io({
  path: '/battleship/socket.io'
});

function App() {
  // --- STATE MANAGEMENT ---
  const [username, setUsername] = useState('');
  const [hasSetName, setHasSetName] = useState(false); // Tracks if the user has submitted their name
  const [gameState, setGameState] = useState('lobby'); // lobby, main_menu, finding_public, waiting_private, playing, game_over
  const [message, setMessage] = useState('Enter your name to begin.');
  
  // Game-specific state
  const [roomId, setRoomId] = useState(null); // Will hold either the UUID or the private room code
  const [joinCodeInput, setJoinCodeInput] = useState(''); // For the "Join Private Lobby" input field
  const [myBoard, setMyBoard] = useState([]);
  const [opponentViewBoard, setOpponentViewBoard] = useState([]);
  const [isMyTurn, setIsMyTurn] = useState(false);
  const [winner, setWinner] = useState(null);
  const [finalOpponentBoard, setFinalOpponentBoard] = useState(null);


  // --- SIDE EFFECTS (SOCKET EVENT LISTENERS) ---
  useEffect(() => {
    // Listen for events from the server and update state accordingly
    socket.on('main_menu', () => {
        setGameState('main_menu');
        setMessage('Welcome! Please choose a game mode.');
    });

    socket.on('finding_game', () => {
        setGameState('finding_public');
        setMessage('Searching for an opponent...');
    });

    socket.on('private_lobby_created', (data) => {
        setGameState('waiting_private');
        setRoomId(data.room_code); // Here, roomId is the shareable code
        setMessage(`Private lobby created. Share this code with a friend:`);
    });

    socket.on('game_started', (data) => {
        setGameState('playing');
        setRoomId(data.room_id);
        setMyBoard(data.my_board);
        setOpponentViewBoard(data.opponent_view_board);
        setIsMyTurn(data.is_my_turn);
        setMessage(data.is_my_turn ? "Your turn!" : `Waiting for ${data.opponent_name}...`);
    });

    socket.on('update_game_state', (data) => {
        setMyBoard(data.my_board);
        setOpponentViewBoard(data.opponent_view_board);
        setIsMyTurn(data.is_my_turn);
        setMessage(data.message);
    });

    socket.on('game_over', (data) => {
        setGameState('game_over');
        setWinner(data.winner_name);
        setFinalOpponentBoard(data.opponent_board);
        setMessage(`${data.winner_name} wins!`);
    });
    
    socket.on('opponent_disconnected', (data) => {
        setMessage(data.message);
        setGameState('main_menu'); // Or a custom 'opponent_left' state
    });

    socket.on('error', (data) => {
        // Show error messages from the server (e.g., invalid room code)
        alert(data.message);
    });
    
    // Cleanup listeners when the component unmounts to prevent memory leaks
    return () => {
      socket.off('main_menu');
      socket.off('finding_game');
      socket.off('private_lobby_created');
      socket.off('game_started');
      socket.off('update_game_state');
      socket.off('game_over');
      socket.off('opponent_disconnected');
      socket.off('error');
    };
  }, []); // Empty dependency array means this effect runs only once on mount


  // --- EVENT HANDLERS (Functions that emit events to the server) ---
  const handleNameSubmit = () => {
    if (username.trim()) {
      socket.emit('register_player', { username });
      setHasSetName(true);
      setGameState('main_menu');
      setMessage('Welcome! Please choose a game mode.');
    } else {
      alert('Please enter a valid username.');
    }
  };

  const handlePlayRandom = () => socket.emit('find_game', { username });
  const handleCancelFindGame = () => socket.emit('cancel_find_game');
  const handleCreatePrivate = () => socket.emit('create_private_lobby');
  const handleJoinPrivate = () => {
    if (joinCodeInput.trim()) {
      // We also need to send the username in case this is the first event the user sends
      socket.emit('join_private_lobby', { room_code: joinCodeInput, username });
    } else {
      alert('Please enter a lobby code.');
    }
  };

  const handleCellClick = (row, col) => {
    if (isMyTurn && gameState === 'playing') {
      socket.emit('make_move', { room_id: roomId, row, col });
    }
  };
  
  const playAgain = () => {
    setGameState('main_menu');
    setMessage('Welcome! Please choose a game mode.');
    // Reset all game-specific states
    setRoomId(null);
    setMyBoard([]);
    setOpponentViewBoard([]);
    setWinner(null);
    setFinalOpponentBoard(null);
  }

  // --- RENDER LOGIC (Decides what to show on the screen) ---
  const renderContent = () => {
    if (!hasSetName) {
      return (
        <div className="lobby">
          <h1>Battleship Online</h1>
          <p>A classic naval combat game. Sink all five of your opponent's ships to win!</p>
          <input
            type="text"
            placeholder="Enter your username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleNameSubmit()}
          />
          <button onClick={handleNameSubmit}>Enter</button>
        </div>
      );
    }

    switch (gameState) {
      case 'main_menu':
        return (
          <div className="main-menu">
            <h2>Main Menu</h2>
            <button onClick={handlePlayRandom}>Play Random Opponent</button>
            <button onClick={handleCreatePrivate}>Create Private Lobby</button>
            <div className="join-lobby">
              <input 
                type="text" 
                placeholder="Enter Lobby Code" 
                value={joinCodeInput} 
                onChange={(e) => setJoinCodeInput(e.target.value.toUpperCase())}
                maxLength="5"
              />
              <button onClick={handleJoinPrivate}>Join Lobby</button>
            </div>
          </div>
        );
      
      case 'finding_public':
        return (
          <div className="game-status">
            <div className="spinner"></div>
            <h1>Searching for Opponent...</h1>
            <button onClick={handleCancelFindGame}>Cancel</button>
          </div>
        );
        
      case 'waiting_private':
        return (
          <div className="game-status">
            <h2>Private Lobby</h2>
            <p>{message}</p>
            <div className="room-code">{roomId}</div>
            <p>Waiting for opponent to join...</p>
          </div>
        );
        
      case 'playing':
        return (
          <div className="game-area">
            <div className="boards-wrapper">
              <div className="board-container">
                <h2>Your Board</h2>
                <Board boardData={myBoard} isOpponentBoard={false} />
              </div>
              <div className="board-container">
                <h2>Opponent's Board</h2>
                <Board 
                  boardData={opponentViewBoard} 
                  onCellClick={handleCellClick}
                  isOpponentBoard={true}
                />
              </div>
            </div>
          </div>
        );

      case 'game_over':
        return (
          <div className="game-area">
            <div className="boards-wrapper">
              <div className="board-container">
                  <h2>Your Final Board</h2>
                  <Board boardData={myBoard} isOpponentBoard={false} />
              </div>
              <div className="board-container">
                  <h2>Opponent's Final Board</h2>
                  <Board 
                      boardData={finalOpponentBoard} 
                      isOpponentBoard={true}
                  />
              </div>
            </div>
            <div className="game-over-modal">
              <h1>Game Over</h1>
              <h2>{winner === username ? "You Win!" : "You Lose!"}</h2>
              <button onClick={playAgain}>Play Again</button>
            </div>
          </div>
        );

      default:
        return <div>Loading...</div>;
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="status-message">
          {/* We only show the main message when not in the game boards view */}
          {(gameState !== 'playing' && gameState !== 'game_over') ? <h1>{message}</h1> : <p>{message}</p>}
        </div>
      </header>
      <main className="main-content">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;