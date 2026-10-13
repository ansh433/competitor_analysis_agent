import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

function App(): React.JSX.Element {
  return (
    <main className="min-h-screen bg-stone-950 text-stone-50">
      <h1>Compass Intelligence</h1>
    </main>
  );
}

const root = document.getElementById("root");
if (!root) throw new Error("Missing root element");
createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

