/**
 * API client for Consent Guard backend.
 *
 * All communication with the FastAPI backend goes through here.
 * Polling-based (2-second interval) for simplicity — SSE or
 * WebSockets would be better for production, but polling is
 * adequate for a demo with a single reviewer.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface Flag {
  category: string;
  confidence: number;
  quoted_span: string;
  cleared_by_allowlist: boolean;
  suggested_rewrite?: string;
}

export interface Decision {
  id: string;
  timestamp: string;
  message_id: string;
  flags: Flag[];
  action: 'sent' | 'held' | 'approved' | 'rejected';
  reviewer_id?: string;
  review_notes?: string;
}

export interface MessageWithDecision {
  id: string;
  content: string;
  agent_id: string;
  timestamp: string;
  decision: Decision | null;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  message_id: string;
  flags: Flag[];
  action: string;
  reviewer_id?: string;
}

/**
 * Intercept an agent message — run it through the classification pipeline.
 */
export async function interceptMessage(
  content: string,
  agentId: string = 'demo-agent'
): Promise<MessageWithDecision> {
  const res = await fetch(`${API_BASE}/intercept`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, agent_id: agentId }),
  });

  if (!res.ok) {
    throw new Error(`Intercept failed: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

/**
 * Fetch all processed messages.
 */
export async function getMessages(): Promise<MessageWithDecision[]> {
  const res = await fetch(`${API_BASE}/messages`);
  if (!res.ok) throw new Error(`Failed to fetch messages: ${res.status}`);
  return res.json();
}

/**
 * Fetch messages held for review.
 */
export async function getReviewQueue(): Promise<MessageWithDecision[]> {
  const res = await fetch(`${API_BASE}/review`);
  if (!res.ok) throw new Error(`Failed to fetch review queue: ${res.status}`);
  return res.json();
}

/**
 * Approve a held message.
 */
export async function approveMessage(
  messageId: string,
  reviewerId: string = 'reviewer-1'
): Promise<void> {
  const res = await fetch(`${API_BASE}/review/${messageId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer_id: reviewerId }),
  });

  if (!res.ok) throw new Error(`Approve failed: ${res.status}`);
}

/**
 * Reject a held message.
 */
export async function rejectMessage(
  messageId: string,
  reviewerId: string = 'reviewer-1'
): Promise<void> {
  const res = await fetch(`${API_BASE}/review/${messageId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer_id: reviewerId }),
  });

  if (!res.ok) throw new Error(`Reject failed: ${res.status}`);
}

/**
 * Fetch the audit log.
 */
export async function getAuditLog(limit: number = 200): Promise<AuditLogEntry[]> {
  const res = await fetch(`${API_BASE}/audit-log?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch audit log: ${res.status}`);
  return res.json();
}

/**
 * Reset all state (demo only).
 */
export async function resetState(): Promise<void> {
  const res = await fetch(`${API_BASE}/reset`, { method: 'POST' });
  if (!res.ok) throw new Error(`Reset failed: ${res.status}`);
}

/**
 * Format a category slug to human-readable form.
 * "false_urgency" → "False Urgency"
 */
export function formatCategory(category: string): string {
  return category
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Format an ISO timestamp to a short time string.
 */
export function formatTime(isoTimestamp: string): string {
  try {
    const date = new Date(isoTimestamp);
    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch {
    return isoTimestamp;
  }
}

/**
 * Subscribe to the real-time SSE stream for instant updates.
 */
export function subscribeToEvents(onEvent: (eventPayload: any) => void): () => void {
  const eventSource = new EventSource(`${API_BASE}/stream`);
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onEvent(data);
    } catch (err) {
      console.error("Failed to parse SSE payload", err);
    }
  };
  eventSource.onerror = (err) => {
    console.error("SSE Error:", err);
  };
  return () => {
    eventSource.close();
  };
}
