/** Typed wrapper over all Mia FastAPI endpoints. */
export type ChatMode = 'auto' | 'general' | 'coding' | 'sql' | 'diagram' | 'chart' | 'ui';

export interface ChatResult {
  reply: string;
  mode: string;
  artifact: Record<string, unknown> | null;
  session_id: string;
}

export interface ChatMsg {
  role: 'user' | 'assistant';
  content: string;
  mode?: string;
  artifact?: Record<string, unknown> | null;
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json() as Promise<T>;
}

export const api = {
  health: () => req<{ status: string }>('/health'),
  chat: (message: string, session_id = 'default', mode: ChatMode = 'auto') =>
    req<ChatResult>('/api/chat/', {
      method: 'POST',
      body: JSON.stringify({ message, session_id, mode }),
    }),
  history: (session_id = 'default') =>
    req<{ session_id: string; messages: ChatMsg[] }>(`/api/chat/history/${encodeURIComponent(session_id)}`),
  runCode: (source: string) =>
    req<{ ok: boolean; result?: string; error?: string }>('/api/chat/run-code', {
      method: 'POST',
      body: JSON.stringify({ source }),
    }),
  runSql: (sql: string) =>
    req<{ ok: boolean; columns?: string[]; rows?: Record<string, unknown>[]; error?: string }>(
      '/api/chat/run-sql',
      { method: 'POST', body: JSON.stringify({ sql }) },
    ),

  avatarStyles: () => req<{ styles: string[] }>('/api/avatar/styles'),
  avatarGenerate: (body: { prompt: string; style?: string; seed?: number | null; character_ref?: string | null }) =>
    req<{ ok: boolean; url?: string; path?: string; stub?: boolean; seed?: number; prompt?: string; error?: string; note?: string }>(
      '/api/avatar/generate',
      { method: 'POST', body: JSON.stringify(body) },
    ),
  avatarRender: (body: { prompt: string; seed?: number | null }) =>
    req<{ ok: boolean; url?: string; error?: string; note?: string }>('/api/avatar/render', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  avatarProfiles: () => req<{ profiles: Record<string, unknown> }>('/api/avatar/profiles'),
  avatarSaveProfile: (body: { name: string; prompt: string; style: string; seed?: number | null; character_ref?: string | null }) =>
    req<{ ok: boolean; name: string }>('/api/avatar/profiles', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  renderPreview: (body: { label?: string; prompt?: string; frames?: number; fps?: number }) =>
    req<{ ok: boolean; url: string; frames: number; fps: number }>('/api/render/preview', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  remindersList: () =>
    req<{ reminders: Reminder[] }>('/api/reminders/'),
  reminderCreate: (body: { title: string; body?: string; due_at?: string | null; channel?: string }) =>
    req<{ reminder: Reminder }>('/api/reminders/', { method: 'POST', body: JSON.stringify(body) }),
  reminderDelete: (id: number) => req<{ ok: boolean }>(`/api/reminders/${id}`, { method: 'DELETE' }),
  reminderDispatch: (id: number) =>
    req<{ id: number; delivered: boolean; dispatch: unknown }>(`/api/reminders/${id}/dispatch`, {
      method: 'POST',
    }),
  remindersPollDue: () =>
    req<{ checked: number; results: unknown[] }>('/api/reminders/poll-due', { method: 'POST' }),

  videoSignal: (body: { session_id: string; peer_id: string; kind: string; payload?: Record<string, unknown> }) =>
    req<{ ok: boolean; event?: unknown }>(`/api/video/signal`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  videoHistory: (session_id: string) =>
    req<{ session_id: string; peers: string[]; events: SignalEvent[] }>(
      `/api/video/history/${encodeURIComponent(session_id)}`,
    ),
  dailyBriefing: (focus = 'day overview') =>
    req<Briefing>(`/api/video/daily-briefing`, {
      method: 'POST',
      body: JSON.stringify({ focus }),
    }),
};

export interface Reminder {
  id: number;
  title: string;
  body: string;
  due_at: string | null;
  channel: string;
  delivered: boolean;
}

export interface SignalEvent {
  session_id: string;
  from: string;
  kind: string;
  payload: Record<string, unknown>;
  ts: number;
}

export interface Briefing {
  date: string;
  focus: string;
  script: string;
  talking_points: string[];
  voice: { voice: string; rate: number; pitch: number };
  video: { avatar_style: string; frames: number; fps: number };
  preview: { ok: boolean; url: string };
}
