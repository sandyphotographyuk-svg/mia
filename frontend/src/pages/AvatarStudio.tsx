import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useMia } from '../store/useMia';

export default function AvatarStudio() {
  const { avatarUrl, setAvatarUrl, characterRef, setCharacterRef } = useMia();
  const [prompt, setPrompt] = useState('Mia, friendly engineer companion, shoulder-length dark hair, warm smile');
  const [style, setStyle] = useState('portrait');
  const [styles, setStyles] = useState<string[]>(['portrait']);
  const [seed, setSeed] = useState(42);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');
  const [profiles, setProfiles] = useState<Record<string, unknown>>({});
  const [profileName, setProfileName] = useState('mia-default');
  const [showRender, setShowRender] = useState(false);

  useEffect(() => {
    api.avatarStyles().then((s) => setStyles(s.styles)).catch(() => undefined);
    api.avatarProfiles().then((p) => setProfiles(p.profiles)).catch(() => undefined);
  }, []);

  const generate = async () => {
    setBusy(true);
    setMsg('');
    try {
      const r = await api.avatarGenerate({ prompt, style, seed, character_ref: characterRef });
      if (r.ok && r.url) {
        setAvatarUrl(r.url);
        setMsg(r.stub ? 'Placeholder render (set HUGGINGFACE_API_KEY for real images).' : 'Rendered OK');
      } else {
        setMsg(r.error || 'Render failed');
      }
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'backend offline');
    } finally {
      setBusy(false);
    }
  };

  const saveProfile = async () => {
    try {
      await api.avatarSaveProfile({ name: profileName, prompt, style, seed, character_ref: characterRef });
      const p = await api.avatarProfiles();
      setProfiles(p.profiles);
      setMsg('Profile saved: ' + profileName);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'save failed');
    }
  };

  return (
    <section className="rounded border border-slate-800 p-3">
      <h2 className="mb-2 font-semibold">Avatar Studio</h2>
      {avatarUrl && <img src={avatarUrl} alt="Mia avatar" className="mb-2 max-h-72 rounded border border-slate-700" />}
      <textarea
        className="w-full rounded bg-slate-900 p-2 text-sm"
        rows={2}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />
      <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
        <label>Style
          <select className="ml-1 rounded bg-slate-900 p-1" value={style} onChange={(e) => setStyle(e.target.value)}>
            {styles.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <label>Seed
          <input type="number" className="ml-1 w-24 rounded bg-slate-900 p-1" value={seed} onChange={(e) => setSeed(Number(e.target.value))} />
        </label>
        <label className="col-span-2">Character ref
          <input className="ml-1 w-40 rounded bg-slate-900 p-1" value={characterRef} onChange={(e) => setCharacterRef(e.target.value)} />
        </label>
      </div>
      <div className="mt-2 flex gap-2">
        <button className="rounded bg-sky-600 px-3 py-1 text-sm disabled:opacity-50" disabled={busy} onClick={generate}>
          {busy ? 'Rendering...' : 'Generate avatar'}
        </button>
        <button className="rounded bg-slate-700 px-3 py-1 text-sm" onClick={() => setShowRender((v) => !v)}>
          {showRender ? 'Hide design render' : 'Design render'}
        </button>
      </div>
      {showRender && <DesignRender />}
      <div className="mt-2 flex gap-2 text-sm">
        <input className="flex-1 rounded bg-slate-900 p-1" value={profileName} onChange={(e) => setProfileName(e.target.value)} placeholder="profile name" />
        <button className="rounded bg-emerald-700 px-3 py-1" onClick={saveProfile}>Save profile</button>
      </div>
      {Object.keys(profiles).length > 0 && (
        <div className="mt-1 text-xs text-slate-400">Profiles: {Object.keys(profiles).join(', ')}</div>
      )}
      {msg && <div className="mt-1 text-xs text-slate-300">{msg}</div>}
    </section>
  );
}

function DesignRender() {
  const [dprompt, setDprompt] = useState('home lab server rack, front view');
  const [url, setUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const go = async () => {
    setBusy(true);
    try {
      const r = await api.avatarRender({ prompt: dprompt });
      if (r.ok && r.url) setUrl(r.url);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="mt-2 rounded border border-slate-700 p-2">
      <div className="text-sm font-medium">Schematic / design render</div>
      <div className="mt-1 flex gap-2">
        <input className="flex-1 rounded bg-slate-900 p-1 text-sm" value={dprompt} onChange={(e) => setDprompt(e.target.value)} />
        <button className="rounded bg-slate-600 px-2 text-sm disabled:opacity-50" disabled={busy} onClick={go}>
          {busy ? '...' : 'Render'}
        </button>
      </div>
      {url && <img src={url} alt="design render" className="mt-1 max-h-56 rounded" />}
    </div>
  );
}
