import { useState } from "react";

function App() {
  

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Electron + Vite + React + TailwindCSS</h1>
      <button
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        onClick={() => {
          console.log("Button clicked!");
        }}
      >
        Click Me
      </button>
    </div>
  );
}

export default App;
