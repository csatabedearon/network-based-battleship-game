import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import Board from './components/Board';

// Connect to the backend server.
// Use 'http://localhost:5001' for local development.
// When deploying, you'll change this to your actual server's address.
const socket = io('http://localhost:5001');

function App() {
  // --- STATE MANAGEMENT ---
  const [username, setUsername] = useState('');
  const [isConnected, setIsConnected] = useState(socket.connected);
  const [gameState, setGameState] =useState('lobby'); // lobby, finding, playing, game_over
  const [message, setMessage] = useState('Enter your name to begin.');
  
  // Game-specific state
  const [roomId, setRoomId] = useState(null);
  const [myBoard, setMyBoard] = useState([]);
  const [opponentViewBoard, setOpponentViewBoard] = useState([]);
  const [isMyTurn, setIsMyTurn] = useState(false);
  const [winner, setWinner] = useState(null);
  const [finalOpponentBoard, setFinalOpponentBoard] = useState(null);


  // --- SIDE EFFECTS ---
  // This useEffect hook runs once when the component mounts.
  // It's used for setting up event listeners on the socket.
  useEffect(() => {
    // --- SOCKET EVENT LISTENERS ---
    socket.on('connect', () => setIsConnected(true));
    socket.on('disconnect', () => setIsConnected(false));

    socket.on('finding_game', (data) => {
      setGameState('finding');
      setMessage(data.message);
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

    socket.on('error', (data) => {
      // Show error messages from the server
      setMessage(data.message);
    });
    
    // --- CLEANUP ---
    // This function is returned by useEffect and runs when the component unmounts.
    // It's important for preventing memory leaks.
    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('finding_game');
      socket.off('game_started');
      socket.off('update_game_state');
      socket.off('game_over');
      socket.off('error');
    };
  }, []); // The empty dependency array [] means this effect runs only once.


  // --- EVENT HANDLERS ---
  const handleFindGame = () => {
    if (username.trim() !== '') {
      socket.emit('find_game', { username });
    } else {
      setMessage('Please enter a valid username.');
    }
  };

  const handleCellClick = (row, col) => {
    // A cell on the opponent's board was clicked.
    // Only send a move if it's currently our turn.
    if (isMyTurn) {
      socket.emit('make_move', { room_id: roomId, row, col });
    }
  };

  // --- RENDER LOGIC ---
  const renderContent = () => {
    switch (gameState) {
      case 'finding':
        return <div className="game-status"><h1>Searching for Opponent...</h1><p>{message}</p></div>;
      
      case 'playing':
      case 'game_over':
        return (
          <div className="game-area">
            <div className="board-container">
              <h2>Your Board</h2>
              <Board boardData={myBoard} isOpponentBoard={false} />
            </div>
            <div className="board-container">
              <h2>Opponent's Board</h2>
              <Board 
                boardData={gameState === 'game_over' ? finalOpponentBoard : opponentViewBoard} 
                onCellClick={handleCellClick}
                isOpponentBoard={true}
              />
            </div>
          </div>
        );
      
      default: // 'lobby'
        return (
          <div className="lobby">
            <h1>Battleship Online</h1>
            <input
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleFindGame()}
            />
            <button onClick={handleFindGame}>Find Game</button>
          </div>
        );
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="status-message">
          <p>{message}</p>
        </div>
      </header>
      <main className="main-content">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;