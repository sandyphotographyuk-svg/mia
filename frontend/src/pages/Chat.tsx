import { useEffect, useRef, useState } from 'react';
import Message from '../components/Message';
import { api, type ChatMode } from '../lib/api';
import { useMia } from '../store/useMia';

const MODES: ChatMode[] = ['auto', 'general', 'coding', 'sql', 'diagram', 'chart', 'ui'];

export default function Chat() {
  const { sessionId, setSessionId, messages, setMessages, pushMessage } = useMia();
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<ChatMode>('auto');
  const [busy, setBusy] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.history(sessionId).then((h) => setMessages(h.messages)).catch(() => undefined);
  }, [sessionId, setMessages]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    pushMessage({ role: 'user', content: text });
    setInput('');
    try {
      const r = await api.chat(text, sessionId, mode);
      pushMessage({ role: 'assistant', content: r.reply, mode: r.mode, artifact: r.artifact });
    } catch {
      pushMessage({ role: 'assistant', content: '(backend offline - start FastAPI on :8000)' });
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="flex flex-col rounded border border-slate-800 p-3">
      <div className="mb-2 flex items-center gap-2">
        <h2 className="font-semibold">Chat</h2>
        <input
          className="w-28 rounded bg-slate-900 px-2 py-1 text-xs"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          title="session id"
        />
        <select
          className="rounded bg-slate-900 px-2 py-1 text-xs"
          value={mode}
          onChange={(e) => setMode(e.target.value as ChatMode)}
          title="response mode"
        >
          {MODES.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </div>
      <div className="flex h-96 flex-col gap-2 overflow-auto">
        {messages.map((m, i) => (
          <Message key={i} role={m.role} content={m.content} mode={m.mode} artifact={m.artifact} />
        ))}
        <div ref={bottom} />
      </div>
      <div className="mt-2 flex gap-2">
        <input
          className="flex-1 rounded bg-slate-900 p-2 text-sm"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') send(); }}
          placeholder="Ask Mia to code, query SQL, draw diagrams, chart, design UI..."
        />
        <button className="rounded bg-sky-600 px-4 disabled:opacity-50" disabled={busy} onClick={send}>
          {busy ? '...' : 'Send'}
        </button>
      </div>
    </section>
  );
}

