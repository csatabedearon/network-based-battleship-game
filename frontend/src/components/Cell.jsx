import React from 'react';

// The Cell component receives props: value, onClick, and isOpponentBoard
function Cell({ value, onClick, isOpponentBoard }) {
  // Determine the CSS class based on the cell's value
  const getCellClass = () => {
    switch (value) {
      case 'S':
        // Only show ships on the player's own board, not the opponent's view
        return isOpponentBoard ? 'water' : 'ship';
      case 'X':
        return 'hit';
      case 'O':
        return 'miss';
      default:
        return 'water';
    }
  };

  return (
    <div
      className={`cell ${getCellClass()}`}
      onClick={onClick}
    />
  );
}

export default Cell;