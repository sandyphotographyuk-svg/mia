import { useEffect, useRef } from 'react';

let mermaidReady: Promise<unknown> | null = null;

async function ensureMermaid() {
  if (!mermaidReady) {
    mermaidReady = import('mermaid').then((m) => {
      m.default.initialize({ startOnLoad: false, theme: 'dark' });
      return m.default;
    });
  }
  return mermaidReady;
}

export default function Mermaid({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const mermaid = (await ensureMermaid()) as {
          render: (id: string, code: string) => Promise<{ svg: string }>;
        };
        const id = `mmd-${Math.random().toString(36).slice(2, 9)}`;
        const { svg } = await mermaid.render(id, code);
        if (alive && ref.current) ref.current.innerHTML = svg;
      } catch {
        if (alive && ref.current) ref.current.innerHTML = `<pre>Invalid mermaid syntax</pre>`;
      }
    })();
    return () => {
      alive = false;
    };
  }, [code]);

  return <div ref={ref} className="overflow-auto rounded bg-slate-900 p-2" />;
}
