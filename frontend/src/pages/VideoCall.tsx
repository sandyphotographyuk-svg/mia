import { useEffect, useRef, useState } from 'react';
import { io, type Socket } from 'socket.io-client';
import { api, type Briefing, type SignalEvent } from '../lib/api';

const PEER = 'browser-' + Math.random().toString(36).slice(2, 8);

export default function VideoCall() {
  const [sessionId] = useState('daily');
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [focus, setFocus] = useState('day overview');
  const [busy, setBusy] = useState(false);
  const [events, setEvents] = useState<SignalEvent[]>([]);
  const [status, setStatus] = useState('idle');
  const [localOn, setLocalOn] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sockRef = useRef<Socket | null>(null);

  useEffect(() => {
    api.videoHistory(sessionId).then((h) => setEvents(h.events)).catch(() => undefined);
    let sock: Socket | null = null;
    try {
      sock = io({ path: '/ws/socket.io' });
      sockRef.current = sock;
      sock.on('connect', () => setStatus('socket connected'));
      sock.on('mia:signal', (ev: SignalEvent) => setEvents((e) => [...e.slice(-49), ev]));
      sock.emit('mia:join', { session_id: sessionId, peer_id: PEER });
    } catch {
      setStatus('socket unavailable (REST fallback)');
    }
    return () => {
      sock?.disconnect();
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, [sessionId]);

  const loadBriefing = async () => {
    setBusy(true);
    try {
      const b = await api.dailyBriefing(focus);
      setBriefing(b);
      await api.videoSignal({ session_id: sessionId, peer_id: PEER, kind: 'briefing', payload: { focus } });
      const h = await api.videoHistory(sessionId);
      setEvents(h.events);
    } finally {
      setBusy(false);
    }
  };

  const toggleCamera = async () => {
    if (localOn) {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      if (videoRef.current) videoRef.current.srcObject = null;
      setLocalOn(false);
      return;
    }
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      streamRef.current = s;
      if (videoRef.current) videoRef.current.srcObject = s;
      setLocalOn(true);
    } catch {
      setStatus('camera blocked - check browser permissions');
    }
  };

  const speak = () => {
    if (!briefing || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(briefing.script);
    u.rate = briefing.voice.rate;
    u.pitch = briefing.voice.pitch;
    window.speechSynthesis.speak(u);
  };

  return (
    <section className="rounded border border-slate-800 p-3">
      <h2 className="mb-2 font-semibold">Daily Video Call</h2>
      <div className="mb-2 flex gap-2 text-sm">
        <input className="flex-1 rounded bg-slate-900 p-1" value={focus} onChange={(e) => setFocus(e.target.value)} placeholder="briefing focus" />
        <button className="rounded bg-sky-600 px-3 py-1 disabled:opacity-50" disabled={busy} onClick={loadBriefing}>
          {busy ? '...' : 'Load briefing'}
        </button>
      </div>
      {briefing && (
        <div className="mb-2 rounded bg-slate-900 p-2 text-sm">
          <div className="text-xs text-slate-400">{briefing.date} - {briefing.focus}</div>
          <ul className="mt-1 list-disc pl-4">
            {briefing.talking_points.map((t, i) => <li key={i}>{t}</li>)}
          </ul>
          {briefing.preview?.url && <img src={briefing.preview.url} alt="Mia preview" className="mt-1 max-h-40 rounded" />}
          <button className="mt-1 rounded bg-emerald-700 px-2 py-0.5 text-xs" onClick={speak}>Speak briefing</button>
        </div>
      )}
      <div className="flex gap-2">
        <video ref={videoRef} autoPlay muted playsInline className="h-36 w-48 rounded bg-black" />
        <div className="flex-1 text-xs">
          <div className="mb-1 text-slate-400">status: {status} - peer {PEER}</div>
          <button className="rounded bg-slate-700 px-2 py-1" onClick={toggleCamera}>
            {localOn ? 'Stop camera' : 'Start camera'}
          </button>
          <div className="mt-1 max-h-28 overflow-auto">
            {events.slice(-8).map((e, i) => (
              <div key={i} className="text-slate-400">{e.kind} from {e.from}</div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

