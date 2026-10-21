import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { getStats, listTickets, UnauthorizedError } from "./api";
import type { Credentials } from "./api";
import type { Stats, TicketHR } from "./types";
import TicketDetail from "./TicketDetail";

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
    <div className="card narrow">
      <h2>HR login</h2>
      <form onSubmit={handleSubmit}>
        <label>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        <button type="submit" className="primary">Log in</button>
      </form>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

function percent(value: number | null): string {
  return value === null ? "–" : `${Math.round(value * 100)}%`;
}

function TicketTable({
  tickets,
  onSelect,
}: {
  tickets: TicketHR[];
  onSelect: (id: number) => void;
}) {
  if (tickets.length === 0) {
    return <p className="muted">No tickets match these filters.</p>;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Received</th>
            <th>Category</th>
            <th>Urgency</th>
            <th>Summary</th>
            <th>Review</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr
              key={t.id}
              className={t.needs_review ? "review" : ""}
              onClick={() => onSelect(t.id)}
            >
              <td>{t.id}</td>
              <td className="muted">
                {new Date(t.created_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}
              </td>
              <td><span className="badge">{t.category ?? "failed"}</span></td>
              <td><span className={`badge ${t.urgency ?? ""}`}>{t.urgency ?? "-"}</span></td>
              <td>{t.summary ?? "-"}</td>
              <td>
                {t.needs_review ? (
                  <>
                    <span className="badge review">Review</span>
                    <div className="muted">{t.review_reasons.join("; ")}</div>
                  </>
                ) : (
                  <span className="muted">-</span>
                )}
              </td>
              <td>
                <span className={`badge ${t.status === "approved" ? "approved" : ""}`}>{t.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function HRDashboard() {
  const [credentials, setCredentials] = useState<Credentials | null>(null);
  const [queue, setQueue] = useState("");
  const [status, setStatus] = useState("new");
  const [tickets, setTickets] = useState<TicketHR[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);   // null = show the list

  // Load the list and the stats when the login or a filter changes,
  // and again when Lisa comes back from a ticket
  useEffect(() => {
    if (!credentials || selectedId !== null) return; // Don't load if no login was made (quits the whole HR function)
    setLoading(true);
    setError(null);
    Promise.all([listTickets(credentials, { queue, status }), getStats(credentials)]) // Start both requests (list tickets and get stats) at the same time, and wait until both finish.
      .then(([list, newStats]) => {
        setTickets(list);
        setStats(newStats);
      })
      .catch((err: Error) => {
        setError(err.message);
        if (err instanceof UnauthorizedError) setCredentials(null);   // back to the login form
      })
      .finally(() => setLoading(false));
  }, [credentials, queue, status, selectedId]); // reload if any of these change

  if (!credentials) {
    return (
      <>
        {error && <div className="narrow" style={{ marginBottom: 16 }}><p role="alert">{error}</p></div>}
        <HRLogin onLogin={setCredentials} />
      </>
    );
  }

  if (selectedId !== null) {
    return (
      <TicketDetail
        credentials={credentials}
        ticketId={selectedId}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <>
      {stats && (
        <div className="stats">
          <Stat label="Tickets" value={stats.total_tickets} />
          <Stat label="Need review" value={percent(stats.review_rate)} />
          <Stat label="Approved" value={stats.approved_tickets} />
          <Stat label="Drafts edited by HR" value={percent(stats.edited_rate)} />
        </div>
      )}
      <div className="card">
        <div className="dashboard-header">
          <h2>Tickets</h2>
          <span className="muted">{tickets.length} shown · review first</span>
        </div>
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
        {loading ? <p className="muted">Loading...</p> : <TicketTable tickets={tickets} onSelect={setSelectedId} />}
      </div>
    </>
  );
}

export default HRDashboard;