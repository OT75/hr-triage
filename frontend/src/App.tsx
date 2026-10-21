import { useEffect, useState } from "react";
import HRDashboard from "./HRDashboard";
import RequestForm from "./RequestForm";
import type { Credentials } from "./api";

type View = "employee" | "hr";

// Read a saved value from this tab's storage. Falls back if storage is blocked or empty.
function loadSaved<T>(key: string, fallback: T): T {
  try {
    const raw = sessionStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function App() {
  // Lazy initializers: read storage once, on the first render only
  const [view, setView] = useState<View>(() => loadSaved<View>("hr-triage:view", "employee"));
  // Lifted up from HRDashboard: App never unmounts, so switching tabs keeps the login
  const [credentials, setCredentials] = useState<Credentials | null>(() =>
    loadSaved<Credentials | null>("hr-triage:credentials", null),
  );

  // Save the view whenever it changes, so a refresh keeps you on the same tab
  useEffect(() => {
    try {
      sessionStorage.setItem("hr-triage:view", JSON.stringify(view));
    } catch {
      // storage blocked: the app still works, it just forgets on refresh
    }
  }, [view]);

  // Save the login, or remove it on logout / wrong password
  useEffect(() => {
    try {
      if (credentials) {
        sessionStorage.setItem("hr-triage:credentials", JSON.stringify(credentials));
      } else {
        sessionStorage.removeItem("hr-triage:credentials");
      }
    } catch {
      // storage blocked: same as above
    }
  }, [credentials]);

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
          {credentials && (
            <button className="tab" onClick={() => setCredentials(null)}>
              Log out
            </button>
          )}
        </nav>
      </header>
      <main className="container">
        {view === "employee" ? (
          <RequestForm />
        ) : (
          <HRDashboard credentials={credentials} onCredentialsChange={setCredentials} />
        )}
      </main>
    </>
  );
}

export default App;