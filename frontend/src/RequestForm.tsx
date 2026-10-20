import { useState } from "react";
import type { FormEvent } from "react";
import { createRequest } from "./api";
import type { TicketCreated } from "./types";

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
      <section>
        <h2>Request received</h2>
        <p>{ticket.message}</p>
        <p>Your ticket number: <strong>#{ticket.id}</strong></p>
        <button onClick={() => { setTicket(null); setText(""); }}>
          Send another request
        </button>
      </section>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2>Ask HR</h2>
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
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={5} required />
      </label>
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={loading}>
        {loading ? "Sending..." : "Send"}
      </button>
    </form>
  );
}

export default RequestForm;