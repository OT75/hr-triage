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
    return error ? <p role="alert">{error}</p> : <p>Loading...</p>;
  }

  const approved = ticket.status === "approved";

  return (
    <section className="detail">
      <button onClick={onBack}>← Back to list</button>
      <h2>Ticket #{ticket.id} · {ticket.status}</h2>

      {ticket.needs_review && (
        <div className="reasons">
          <strong>Check carefully:</strong> {ticket.review_reasons.join("; ")}
        </div>
      )}

      <h3>Request</h3>
      <p><strong>{ticket.name}</strong> ({ticket.email})</p>
      <p className="request-text">{ticket.text}</p>

      <h3>What the AI understood</h3>
      <p>
        Category: {ticket.category ?? "failed"} · Urgency: {ticket.urgency ?? "-"} ·
        Language: {ticket.language ?? "-"} · Queue: {ticket.queue}
      </p>
      <p>Summary: {ticket.summary ?? "-"}</p>
      {ticket.other_topics.length > 0 && (
        <p>Also asks about: {ticket.other_topics.join(", ")}</p>
      )}

      <h3>Reply</h3>
      <textarea
        value={reply}
        onChange={(e) => setReply(e.target.value)}
        rows={8}
        disabled={approved}
      />

      {error && <p role="alert">{error}</p>}

      {approved ? (
        <p>✓ Approved{ticket.edited ? " (HR edited the draft)" : " (draft used as is)"}</p>
      ) : (
        <div className="actions">
          <button onClick={() => save(false)} disabled={saving}>Save draft</button>
          <button onClick={() => save(true)} disabled={saving}>Approve</button>
        </div>
      )}
    </section>
  );
}

export default TicketDetail;