import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useMia } from '../store/useMia';

export default function Reminders() {
  const { reminders, setReminders } = useMia();
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [dueAt, setDueAt] = useState('');
  const [channel, setChannel] = useState('desktop');
  const [msg, setMsg] = useState('');

  const refresh = async () => {
    try {
      const r = await api.remindersList();
      setReminders(r.reminders);
    } catch {
      setMsg('backend offline');
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const create = async () => {
    if (!title.trim()) return;
    try {
      await api.reminderCreate({
        title: title.trim(),
        body,
        due_at: dueAt ? new Date(dueAt).toISOString() : null,
        channel,
      });
      setTitle('');
      setBody('');
      setDueAt('');
      await refresh();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'create failed');
    }
  };

  const remove = async (id: number) => {
    await api.reminderDelete(id);
    await refresh();
  };

  const dispatchNow = async (id: number) => {
    const r = await api.reminderDispatch(id);
    setMsg(r.delivered ? 'Delivered OK' : 'Dispatch failed - check channel config');
    await refresh();
  };

  const pollDue = async () => {
    const r = await api.remindersPollDue();
    setMsg('Checked ' + r.checked + ' due reminder(s)');
    await refresh();
  };

  return (
    <section className="rounded border border-slate-800 p-3">
      <div className="mb-2 flex items-center gap-2">
        <h2 className="font-semibold">Reminders</h2>
        <button className="rounded bg-slate-700 px-2 py-0.5 text-xs" onClick={pollDue}>Poll due</button>
      </div>
      <div className="grid gap-1 text-sm">
        <input className="rounded bg-slate-900 p-1" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" />
        <input className="rounded bg-slate-900 p-1" value={body} onChange={(e) => setBody(e.target.value)} placeholder="Details (optional)" />
        <div className="flex gap-1">
          <input type="datetime-local" className="flex-1 rounded bg-slate-900 p-1" value={dueAt} onChange={(e) => setDueAt(e.target.value)} />
          <select className="rounded bg-slate-900 p-1" value={channel} onChange={(e) => setChannel(e.target.value)}>
            <option value="desktop">desktop</option>
            <option value="webhook">webhook</option>
            <option value="telegram">telegram</option>
            <option value="all">all</option>
          </select>
          <button className="rounded bg-sky-600 px-3" onClick={create}>Add</button>
        </div>
      </div>
      <ul className="mt-2 max-h-56 space-y-1 overflow-auto text-sm">
        {reminders.map((r) => (
          <li key={r.id} className="flex items-center gap-2 rounded bg-slate-900 p-1">
            <span className={r.delivered ? 'text-slate-500 line-through' : ''}>
              {r.title}{r.due_at ? ' - ' + new Date(r.due_at).toLocaleString() : ''}
            </span>
            <span className="text-xs text-slate-500">[{r.channel}]</span>
            <span className="flex-1" />
            {!r.delivered && (
              <button className="rounded bg-emerald-700 px-1 text-xs" onClick={() => dispatchNow(r.id)}>Send</button>
            )}
            <button className="rounded bg-red-900 px-1 text-xs" onClick={() => remove(r.id)}>x</button>
          </li>
        ))}
        {reminders.length === 0 && <li className="text-xs text-slate-500">No reminders yet.</li>}
      </ul>
      {msg && <div className="mt-1 text-xs text-slate-400">{msg}</div>}
    </section>
  );
}
