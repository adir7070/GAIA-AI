'use client';

import axios from 'axios';

const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({ baseURL, timeout: 30000 });

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('gaia_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('gaia_token');
      if (window.location.pathname !== '/login') window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ----- Error helper --------------------------------------------------------
// FastAPI returns `detail` as a string (HTTPException) OR an array of objects
// (422 validation). Rendering the raw object crashes React, so normalize to text.
export function errMessage(ex: any, fallback = 'שגיאה'): string {
  const d = ex?.response?.data?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map((e) => e?.msg || JSON.stringify(e)).join('; ');
  if (d && typeof d === 'object') return d.msg || JSON.stringify(d);
  return ex?.message || fallback;
}

// ----- Endpoints -----------------------------------------------------------
export type UserOut = { id: number; email: string; display_name?: string | null };

export async function register(email: string, password: string, display_name?: string) {
  const r = await api.post('/auth/register', { email, password, display_name });
  return r.data as { token: string; user: UserOut };
}
export async function login(email: string, password: string) {
  const r = await api.post('/auth/login', { email, password });
  return r.data as { token: string; user: UserOut };
}

export async function startWhatsApp() {
  const r = await api.post('/whatsapp/connect');
  return r.data as { session_id: string; status: string };
}
export async function getQr() {
  const r = await api.get('/whatsapp/qr');
  return r.data as { qr_base64: string | null; status: string };
}
export async function disconnectWhatsApp() {
  await api.delete('/whatsapp/disconnect');
}

export type Contact = { id: number; wa_id: string; name?: string | null; is_group: boolean; allowed: boolean };
export async function listContacts() {
  const r = await api.get('/contacts');
  return r.data as Contact[];
}
export async function syncContacts() {
  const r = await api.post('/contacts/sync');
  return r.data as Contact[];
}
export async function patchContact(id: number, body: Partial<Contact>) {
  const r = await api.patch(`/contacts/${id}`, body);
  return r.data as Contact;
}

export async function generateAi(contact_id: number, incoming_message: string) {
  const r = await api.post('/ai/generate', { contact_id, incoming_message });
  return r.data as {
    suggestion_id: string;
    suggestion: string;
    confidence: number;
    label: 'ANSWER_NOW' | 'ASK_USER_FOR_TEACHING' | 'UNSURE';
  };
}
export async function sendFeedback(suggestion_id: string, edited_text: string, decision: 'approve' | 'edit' | 'skip' = 'edit') {
  await api.post('/ai/feedback', { suggestion_id, edited_text, decision });
}

export async function sendMessage(contact_id: number, text: string) {
  await api.post('/whatsapp/send', { contact_id, text });
}

export async function analyticsSummary() {
  const r = await api.get('/analytics/summary');
  return r.data;
}

// ----- Style profile (how the model understands you) -----------------------
export type StyleTraits = {
  tone?: string;
  formality?: string;
  typical_length?: string;
  emoji_usage?: string;
  slang?: string;
  punctuation?: string;
  languages?: string[];
  personality?: string[];
  common_phrases?: string[];
};
export type StyleProfile = {
  summary: string;
  traits: StyleTraits;
  edited?: boolean;
  updated_at?: string;
};

export async function getStyleProfile() {
  const r = await api.get('/style-profile');
  return r.data as { profile: StyleProfile | null; message_count: number };
}
export async function analyzeStyleProfile() {
  const r = await api.post('/style-profile/analyze');
  return r.data as { profile: StyleProfile };
}
export async function saveStyleProfile(summary: string, traits: StyleTraits) {
  const r = await api.put('/style-profile', { summary, traits });
  return r.data as { profile: StyleProfile };
}
