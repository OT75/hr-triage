const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

import type { RequestIn, TicketCreated, TicketHR } from "./types";

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

function friendlyError(status: number): string {
  if (status === 422) return "Please check your input: a valid email and a short description of your question.";
  if (status === 503) return "The service is busy right now. Please try again in a minute.";
  return `Something went wrong (error ${status}). Please try again.`;
}

export interface Credentials {
  username: string;
  password: string;
}

// A specific error type, so the dashboard can tell "wrong password" apart from other errors
export class UnauthorizedError extends Error {}

function authHeader(credentials: Credentials): string {
  return "Basic " + btoa(`${credentials.username}:${credentials.password}`);
}

export async function listTickets(
  credentials: Credentials,
  filters: { queue?: string; status?: string },
): Promise<TicketHR[]> {
  const params = new URLSearchParams();
  if (filters.queue) params.set("queue_filter", filters.queue);
  if (filters.status) params.set("status_filter", filters.status);

  let response: Response;
  try {
    response = await fetch(`${API_URL}/tickets?${params}`, {
      headers: { Authorization: authHeader(credentials) },
    });
  } catch {
    throw new Error("Can't reach the server. Please check your connection and try again.");
  }

  if (response.status === 401) throw new UnauthorizedError("Wrong username or password.");
  if (!response.ok) throw new Error(friendlyError(response.status));
  return response.json();
}