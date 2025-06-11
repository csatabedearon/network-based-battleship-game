import React from 'react';
import Cell from './Cell';

// The Board component receives props: boardData, onCellClick, and isOpponentBoard
function Board({ boardData, onCellClick, isOpponentBoard }) {
  return (
    <div className="board" data-is-opponent={isOpponentBoard}>
      {}
      {boardData.map((row, rowIndex) => 
        row.map((cellValue, colIndex) => (
          <Cell
            key={`${rowIndex}-${colIndex}`}
            value={cellValue}
            onClick={() => isOpponentBoard && onCellClick(rowIndex, colIndex)}
          />
        ))
      )}
    </div>
  );
}

export default Board;