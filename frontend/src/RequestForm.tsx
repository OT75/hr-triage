import { useState } from "react";
import type { FormEvent } from "react";
import { createRequest } from "./api";
import type { TicketCreated } from "./types";

// One click fills the question: friendly for employees, fast for live demos
const EXAMPLES = [
  "How many vacation days do I have left?",
  "My payslip is missing my overtime.",
  "I need an employment certificate for my landlord.",
];

function RequestForm() {
  // What the employee types
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [text, setText] = useState("");

  // What's happening right now
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ticket, setTicket] = useState<TicketCreated | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();   // stop the browser's default: reloading the page
    setLoading(true);
    setError(null);
    try {
      const result = await createRequest({ name, email, text });
      setTicket(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  // After success: show the receipt instead of the form
  if (ticket) {
    return (
      <div className="card narrow success">
        <h2>Request received</h2>
        <p className="muted">Your ticket number</p>
        <p className="ticket-number">#{ticket.id}</p>
        <p>{ticket.message}</p>
        <button onClick={() => { setTicket(null); setText(""); }}>
          Send another request
        </button>
      </div>
    );
  }

  return (
    <div className="card narrow">
      <h2>Ask HR</h2>
      <p className="muted">Describe your question in any language. HR will reply by email.</p>
      <form onSubmit={handleSubmit}>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Your question
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={6} required />
        </label>
        <div className="chips">
          {EXAMPLES.map((example) => (
            <button type="button" key={example} className="chip" onClick={() => setText(example)}>
              {example}
            </button>
          ))}
        </div>
        {error && <p role="alert">{error}</p>}
        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Sending..." : "Send request"}
        </button>
      </form>
    </div>
  );
}

export default RequestForm;