import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { listTickets, UnauthorizedError } from "./api";
import type { Credentials } from "./api";
import type { TicketHR } from "./types";

// Must match the queue names in backend/app/routing.py
const QUEUES = ["", "payroll", "time-off", "documents", "benefits", "onboarding", "general"];

function HRLogin({ onLogin }: { onLogin: (credentials: Credentials) => void }) {
  const [username, setUsername] = useState("hr");
  const [password, setPassword] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onLogin({ username, password });
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2>HR login</h2>
      <label>
        Username
        <input value={username} onChange={(e) => setUsername(e.target.value)} required />
      </label>
      <label>
        Password
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </label>
      <button type="submit">Log in</button>
    </form>
  );
}

function TicketTable({ tickets }: { tickets: TicketHR[] }) {
  if (tickets.length === 0) {
    return <p>No tickets match these filters.</p>;
  }
  return (
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Received</th>
          <th>Category</th>
          <th>Urgency</th>
          <th>Summary</th>
          <th>Why review?</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {tickets.map((t) => (
          <tr key={t.id} className={t.needs_review ? "review" : ""}>
            <td>{t.id}</td>
            <td>{new Date(t.created_at).toLocaleString()}</td>
            <td>{t.category ?? "failed"}</td>
            <td>{t.urgency ?? "-"}</td>
            <td>{t.summary ?? "-"}</td>
            <td>{t.needs_review ? t.review_reasons.join("; ") : "-"}</td>
            <td>{t.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function HRDashboard() {
  const [credentials, setCredentials] = useState<Credentials | null>(null);
  const [queue, setQueue] = useState("");
  const [status, setStatus] = useState("new");
  const [tickets, setTickets] = useState<TicketHR[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load tickets whenever the login or a filter changes
  useEffect(() => {
    if (!credentials) return;
    setLoading(true);
    setError(null);
    listTickets(credentials, { queue, status })
      .then(setTickets)
      .catch((err: Error) => {
        setError(err.message);
        if (err instanceof UnauthorizedError) setCredentials(null);   // back to the login form
      })
      .finally(() => setLoading(false));
  }, [credentials, queue, status]);

  if (!credentials) {
    return (
      <>
        {error && <p role="alert">{error}</p>}
        <HRLogin onLogin={setCredentials} />
      </>
    );
  }

  return (
    <section className="dashboard">
      <h2>HR tickets</h2>
      <div className="filters">
        <label>
          Queue
          <select value={queue} onChange={(e) => setQueue(e.target.value)}>
            {QUEUES.map((q) => (
              <option key={q} value={q}>{q || "all queues"}</option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="new">new</option>
            <option value="approved">approved</option>
            <option value="">all</option>
          </select>
        </label>
      </div>
      {error && <p role="alert">{error}</p>}
      {loading ? <p>Loading...</p> : <TicketTable tickets={tickets} />}
    </section>
  );
}

export default HRDashboard;