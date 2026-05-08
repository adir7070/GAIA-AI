'use client';

export type WsEvent =
  | { event: 'new_suggestion'; data: NewSuggestion }
  | { event: 'qr_update'; data: { qr_base64: string } }
  | { event: 'session_ready'; data: Record<string, never> };

export type NewSuggestion = {
  suggestion_id: string;
  contact_id: number;
  contact_name: string;
  incoming: string;
  suggestion: string;
  confidence: number;
  label: 'ANSWER_NOW' | 'ASK_USER_FOR_TEACHING' | 'UNSURE';
};

export function connectWs(onEvent: (e: WsEvent) => void): WebSocket | null {
  if (typeof window === 'undefined') return null;
  const token = localStorage.getItem('gaia_token');
  if (!token) return null;
  const base = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  const ws = new WebSocket(`${base}/ws?token=${encodeURIComponent(token)}`);
  ws.onmessage = (m) => {
    try {
      const e = JSON.parse(m.data) as WsEvent;
      onEvent(e);
    } catch {
      /* ignore */
    }
  };
  ws.onclose = () => {
    /* the dashboard hook will re-open */
  };
  return ws;
}
