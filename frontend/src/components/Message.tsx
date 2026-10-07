import { useState } from 'react';
import Mermaid from './Mermaid';
import { api } from '../lib/api';

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/** Minimal markdown: fenced code, inline code, bold, headings, lists, links. XSS-safe via escaping. */
function md(src: string): string {
  const fences: string[] = [];
  let html = esc(src);
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_m, lang, code) => {
    fences.push(
      `<pre class="overflow-auto rounded bg-slate-900 p-2 text-xs"><code data-lang="${esc(lang || 'text')}">${code.trimEnd()}</code></pre>`,
    );
    return `\u0000${fences.length - 1}\u0000`;
  });
  html = html
    .replace(/^### (.*)$/gm, '<h4 class="font-semibold">$1</h4>')
    .replace(/^## (.*)$/gm, '<h3 class="font-semibold">$1</h3>')
    .replace(/^# (.*)$/gm, '<h2 class="font-semibold">$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="rounded bg-slate-800 px-1">$1</code>')
    .replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, '<a class="text-sky-400 underline" href="$2" target="_blank" rel="noreferrer">$1</a>')
    .replace(/^- (.*)$/gm, '<li class="ml-4 list-disc">$1</li>')
    .replace(/\n/g, '<br/>');
  html = html.replace(/\u0000(\d+)\u0000/g, (_m, i) => fences[Number(i)]);
  return html;
}

function fenceLang(src: string): { lang: string; code: string } | null {
  const m = src.match(/```(\w*)\n([\s\S]*?)```/);
  return m ? { lang: (m[1] || 'text').toLowerCase(), code: m[2].trimEnd() } : null;
}

export default function Message({ role, content, mode, artifact }: { role: string; content: string; mode?: string; artifact?: Record<string, unknown> | null }) {
  const [out, setOut] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const isUser = role === 'user';
  const fence = !isUser ? fenceLang(content) : null;
  const mermaidCode =
    mode === 'diagram' && artifact && typeof artifact['mermaid'] === 'string'
      ? (artifact['mermaid'] as string)
      : null;
  const chartPy =
    mode === 'chart' && artifact && typeof artifact['python'] === 'string'
      ? (artifact['python'] as string)
      : null;
  const uiSchema = mode === 'ui' && artifact && typeof artifact['schema'] === 'object' ? artifact['schema'] : null;
  const imageUrl =
    artifact && typeof artifact['image_url'] === 'string'
      ? (artifact['image_url'] as string)
      : artifact && typeof artifact['url'] === 'string' && mode !== 'ui'
        ? (artifact['url'] as string)
        : null;

  const runCode = async (code: string, kind: 'python' | 'sql') => {
    setBusy(true);
    setErr(null);
    setOut(null);
    try {
      const r = kind === 'python' ? await api.runCode(code) : await api.runSql(code);
      setOut(JSON.stringify(r, null, 2));
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={`rounded p-2 text-sm ${isUser ? 'bg-sky-950' : 'bg-slate-900'}`}>
      <div className="mb-1 text-xs uppercase opacity-60">
        {isUser ? 'you' : `mia${mode && mode !== 'general' ? ` · ${mode}` : ''}`}
      </div>
      {mermaidCode ? (
        <Mermaid code={mermaidCode} />
      ) : (
        <div dangerouslySetInnerHTML={{ __html: md(content) }} />
      )}
      {!isUser && fence && (fence.lang === 'python' || fence.lang === 'py') && (
        <button
          className="mt-1 rounded bg-emerald-700 px-2 py-0.5 text-xs disabled:opacity-50"
          disabled={busy}
          onClick={() => runCode(fence.code, 'python')}
        >
          {busy ? 'Running…' : '▶ Run python'}
        </button>
      )}
      {!isUser && fence && fence.lang === 'sql' && (
        <button
          className="mt-1 rounded bg-emerald-700 px-2 py-0.5 text-xs disabled:opacity-50"
          disabled={busy}
          onClick={() => runCode(fence.code, 'sql')}
        >
          {busy ? 'Running…' : '▶ Run SQL'}
        </button>
      )}
      {chartPy && (
        <details className="mt-1">
          <summary className="cursor-pointer text-xs text-slate-400">chart script</summary>
          <pre className="overflow-auto rounded bg-slate-950 p-2 text-xs">{chartPy}</pre>
          <button
            className="mt-1 rounded bg-emerald-700 px-2 py-0.5 text-xs disabled:opacity-50"
            disabled={busy}
            onClick={() => runCode(chartPy, 'python')}
          >
            {busy ? 'Running…' : '▶ Run chart script'}
          </button>
        </details>
      )}
      {uiSchema && (
        <details className="mt-1">
          <summary className="cursor-pointer text-xs text-slate-400">UI schema</summary>
          <pre className="overflow-auto rounded bg-slate-950 p-2 text-xs">
            {JSON.stringify(uiSchema, null, 2)}
          </pre>
        </details>
      )}
      {imageUrl && (
        <img src={imageUrl} alt="Mia render" className="mt-1 max-h-64 rounded border border-slate-700" />
      )}
      {out && <pre className="mt-1 overflow-auto rounded bg-slate-950 p-2 text-xs">{out}</pre>}
      {err && <div className="mt-1 text-xs text-red-400">{err}</div>}
    </div>
  );
}
