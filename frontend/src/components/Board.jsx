import React from 'react';
import Cell from './Cell';

// The Board component receives props: boardData, onCellClick, and isOpponentBoard
function Board({ boardData, onCellClick, isOpponentBoard }) {
  return (
    <div className="board">
      {/* Map through each row of the board data */}
      {boardData.map((row, rowIndex) => (
        <div key={rowIndex} className="board-row">
          {/* Map through each cell in the row */}
          {row.map((cellValue, colIndex) => (
            <Cell
              key={`${rowIndex}-${colIndex}`}
              value={cellValue}
              // Pass the click handler to the Cell, but only if it's the opponent's board
              onClick={() => isOpponentBoard && onCellClick(rowIndex, colIndex)}
              isOpponentBoard={isOpponentBoard}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export default Board;