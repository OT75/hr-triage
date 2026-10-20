import type { RequestIn, Stats, TicketCreated, TicketHR, TicketUpdate } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

// ---------- Errors ----------

// A specific error type, so the dashboard can tell "wrong password" apart from other errors
export class UnauthorizedError extends Error {}

function friendlyError(status: number): string {
  if (status === 404) return "This ticket doesn't exist.";
  if (status === 409) return "This ticket has already been approved.";
  if (status === 422) return "Please check your input: a valid email and a short description of your question.";
  if (status === 503) return "The service is busy right now. Please try again in a minute.";
  return `Something went wrong (error ${status}). Please try again.`;
}

// ---------- Employee side (no login) ----------

export async function getHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

export async function createRequest(data: RequestIn): Promise<TicketCreated> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/requests`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  } catch {
    // fetch only throws when the server can't be reached at all
    throw new Error("Can't reach the server. Please check your connection and try again.");
  }

  if (!response.ok) {
    throw new Error(friendlyError(response.status));
  }
  return response.json();
}

// ---------- HR side (login required) ----------

export interface Credentials {
  username: string;
  password: string;
}

function authHeader(credentials: Credentials): string {
  return "Basic " + btoa(`${credentials.username}:${credentials.password}`);
}

// Every HR call: add the login header, and turn failures into clear errors
async function hrFetch(
  credentials: Credentials,
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: { ...options.headers, Authorization: authHeader(credentials) },
    });
  } catch {
    throw new Error("Can't reach the server. Please check your connection and try again.");
  }
  if (response.status === 401) throw new UnauthorizedError("Wrong username or password.");
  if (!response.ok) throw new Error(friendlyError(response.status));
  return response;
}

export async function listTickets(
  credentials: Credentials,
  filters: { queue?: string; status?: string },
): Promise<TicketHR[]> {
  const params = new URLSearchParams();
  if (filters.queue) params.set("queue_filter", filters.queue);
  if (filters.status) params.set("status_filter", filters.status);
  const response = await hrFetch(credentials, `/tickets?${params}`);
  return response.json();
}

export async function getTicket(credentials: Credentials, id: number): Promise<TicketHR> {
  const response = await hrFetch(credentials, `/tickets/${id}`);
  return response.json();
}

export async function updateTicket(
  credentials: Credentials,
  id: number,
  update: TicketUpdate,
): Promise<TicketHR> {
  const response = await hrFetch(credentials, `/tickets/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  });
  return response.json();
}

export async function getStats(credentials: Credentials): Promise<Stats> {
  const response = await hrFetch(credentials, "/stats");
  return response.json();
}