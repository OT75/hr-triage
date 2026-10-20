// TypeScript versions of the backend schemas (backend/app/schemas.py).
// When a schema changes in the backend, update it here too.

export type Category =
  | "payroll" | "leave" | "documents" | "benefits" | "onboarding" | "other";

export interface RequestIn {
  name: string;
  email: string;
  text: string;
}

export interface TicketCreated {
  id: number;
  message: string;
}

export interface TicketHR {
  id: number;
  created_at: string;           // dates arrive as text in JSON
  name: string;
  email: string;
  text: string;
  category: string | null;
  urgency: string | null;
  language: string | null;
  summary: string | null;
  confidence: number | null;
  other_topics: string[];
  queue: string;
  needs_review: boolean;
  review_reasons: string[];
  draft: string;
  final_reply: string | null;
  status: string;
  edited: boolean;
}

export interface TicketUpdate {
  reply?: string;
  approve?: boolean;
}