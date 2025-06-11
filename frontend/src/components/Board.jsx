import React from 'react';
import Cell from './Cell';

// The Board component receives props: boardData, onCellClick, and isOpponentBoard
function Board({ boardData, onCellClick, isOpponentBoard }) {
  return (
    // We add a 'data-is-opponent' attribute to help with CSS styling (e.g., for the hover effect)
    <div className="board" data-is-opponent={isOpponentBoard}>
      {/* 
        We now map directly to Cell components. 
        The nested map will produce a single flat list of 100 cells,
        which is exactly what the CSS grid layout expects.
      */}
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