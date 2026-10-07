import { create } from 'zustand';
import type { ChatMsg, Reminder } from '../lib/api';

export type Tab = 'chat' | 'avatar' | 'video' | 'reminders';

interface MiaState {
  tab: Tab;
  setTab: (t: Tab) => void;
  sessionId: string;
  setSessionId: (s: string) => void;
  messages: ChatMsg[];
  setMessages: (m: ChatMsg[]) => void;
  pushMessage: (m: ChatMsg) => void;
  reminders: Reminder[];
  setReminders: (r: Reminder[]) => void;
  avatarUrl: string | null;
  setAvatarUrl: (u: string | null) => void;
  characterRef: string;
  setCharacterRef: (c: string) => void;
}

export const useMia = create<MiaState>((set) => ({
  tab: 'chat',
  setTab: (tab) => set({ tab }),
  sessionId: 'default',
  setSessionId: (sessionId) => set({ sessionId }),
  messages: [],
  setMessages: (messages) => set({ messages }),
  pushMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  reminders: [],
  setReminders: (reminders) => set({ reminders }),
  avatarUrl: null,
  setAvatarUrl: (avatarUrl) => set({ avatarUrl }),
  characterRef: 'mia-v1',
  setCharacterRef: (characterRef) => set({ characterRef }),
}));

