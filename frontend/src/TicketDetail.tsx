import { useEffect, useState } from "react";
import { getTicket, updateTicket } from "./api";
import type { Credentials } from "./api";
import type { TicketHR } from "./types";

interface Props {
  credentials: Credentials;
  ticketId: number;
  onBack: () => void;
}

function TicketDetail({ credentials, ticketId, onBack }: Props) {
  const [ticket, setTicket] = useState<TicketHR | null>(null);
  const [reply, setReply] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load the ticket when the page opens
  useEffect(() => {
    getTicket(credentials, ticketId)
      .then((t) => {
        setTicket(t);
        setReply(t.final_reply ?? t.draft);   // Lisa's saved edit, or else the AI draft
      })
      .catch((err: Error) => setError(err.message));
  }, [credentials, ticketId]);

  async function save(approve: boolean) {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateTicket(credentials, ticketId, { reply, approve });
      setTicket(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSaving(false);
    }
  }

  if (!ticket) {
    return error ? <p role="alert">{error}</p> : <p className="muted">Loading...</p>;
  }

  const approved = ticket.status === "approved";

  return (
    <div>
      <button className="link-button" onClick={onBack}>← Back to tickets</button>

      <div className="detail-header">
        <h2>Ticket #{ticket.id}</h2>
        <span className={`badge ${approved ? "approved" : ""}`}>{ticket.status}</span>
        {ticket.urgency && <span className={`badge ${ticket.urgency}`}>{ticket.urgency}</span>}
        {ticket.needs_review && <span className="badge review">Review</span>}
      </div>

      {ticket.needs_review && (
        <div className="reasons">
          <strong>Check carefully:</strong> {ticket.review_reasons.join("; ")}
        </div>
      )}

      <div className="detail-grid">
        <div className="card">
          <h3>Request</h3>
          <p>
            <strong>{ticket.name}</strong>{" "}
            <span className="muted">· {ticket.email} · {new Date(ticket.created_at).toLocaleString()}</span>
          </p>
          <p className="request-text">{ticket.text}</p>

          <h3>What the AI understood</h3>
          <dl className="facts">
            <dt>Category</dt><dd>{ticket.category ?? "failed"}</dd>
            <dt>Queue</dt><dd>{ticket.queue}</dd>
            <dt>Language</dt><dd>{ticket.language ?? "-"}</dd>
            <dt>Summary</dt><dd>{ticket.summary ?? "-"}</dd>
            {ticket.other_topics.length > 0 && (
              <>
                <dt>Also asks about</dt><dd>{ticket.other_topics.join(", ")}</dd>
              </>
            )}
          </dl>
        </div>

        <div className="card">
          <h3>Reply to the employee</h3>
          <textarea
            value={reply}
            onChange={(e) => setReply(e.target.value)}
            rows={12}
            disabled={approved}
            style={{ width: "100%" }}
          />
          {error && <p role="alert" style={{ marginTop: 12 }}>{error}</p>}
          {approved ? (
            <p className="muted">
              ✓ Approved{ticket.edited ? " · HR edited the draft" : " · draft used as is"}
            </p>
          ) : (
            <div className="actions">
              <button onClick={() => save(false)} disabled={saving}>Save draft</button>
              <button className="primary" onClick={() => save(true)} disabled={saving}>Approve</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default TicketDetail;