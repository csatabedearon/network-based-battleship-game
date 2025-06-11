import React from 'react';

// The Cell component is now much simpler. It only needs to know its value and what to do on click.
function Cell({ value, onClick }) {
  // Determine the CSS class based on the cell's value.
  const getCellClass = () => {
    switch (value) {
      case 'S': return 'ship';
      case 'X': return 'hit';
      case 'O': return 'miss';
      default: return 'water';
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