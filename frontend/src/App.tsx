import { useState } from "react";
import HRDashboard from "./HRDashboard";
import RequestForm from "./RequestForm";

function App() {
  const [view, setView] = useState<"employee" | "hr">("employee");

  return (
    <>
      <header className="topbar">
        <div className="brand">HR Triage</div>
        <nav className="tabs">
          <button
            className={view === "employee" ? "tab active" : "tab"}
            onClick={() => setView("employee")}
          >
            Ask HR
          </button>
          <button
            className={view === "hr" ? "tab active" : "tab"}
            onClick={() => setView("hr")}
          >
            HR dashboard
          </button>
        </nav>
      </header>
      <main className="container">
        {view === "employee" ? <RequestForm /> : <HRDashboard />}
      </main>
    </>
  );
}

export default App;