import { useEffect, useState } from 'react';
import Chat from './pages/Chat';
import AvatarStudio from './pages/AvatarStudio';
import VideoCall from './pages/VideoCall';
import Reminders from './pages/Reminders';
import { api } from './lib/api';
import { useMia, type Tab } from './store/useMia';

const TABS: { id: Tab; label: string }[] = [
  { id: 'chat', label: 'Chat' },
  { id: 'avatar', label: 'Avatar Studio' },
  { id: 'video', label: 'Daily Video Call' },
  { id: 'reminders', label: 'Reminders' },
];

export default function App() {
  const { tab, setTab, avatarUrl } = useMia();
  const [health, setHealth] = useState('checking...');

  useEffect(() => {
    api.health()
      .then((h) => setHealth(h.status))
      .catch(() => setHealth('backend offline'));
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex items-center gap-3 border-b border-slate-800 p-4">
        {avatarUrl && <img src={avatarUrl} alt="Mia" className="h-10 w-10 rounded-full border border-slate-700" />}
        <div className="flex-1">
          <h1 className="text-xl font-bold">Mia - Companion Dashboard</h1>
          <p className="text-xs text-slate-400">backend: {health}</p>
        </div>
        <nav className="flex gap-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`rounded px-3 py-1 text-sm ${tab === t.id ? 'bg-sky-600' : 'bg-slate-800'}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-5xl p-4">
        {tab === 'chat' && <Chat />}
        {tab === 'avatar' && <AvatarStudio />}
        {tab === 'video' && <VideoCall />}
        {tab === 'reminders' && <Reminders />}
      </main>
    </div>
  );
}
