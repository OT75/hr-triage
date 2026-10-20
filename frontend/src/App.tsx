import { useState } from "react";
import HRDashboard from "./HRDashboard";
import RequestForm from "./RequestForm";

function App() {
  const [view, setView] = useState<"employee" | "hr">("employee");

  return (
    <main>
      <h1>HR Triage</h1>
      <nav>
        <button onClick={() => setView("employee")} disabled={view === "employee"}>Employee</button>
        <button onClick={() => setView("hr")} disabled={view === "hr"}>HR</button>
      </nav>
      {view === "employee" ? <RequestForm /> : <HRDashboard />}
    </main>
  );
}

export default App;