import { useState } from "react";
import { Send, Loader2 } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { askAtlas, type ChatResponse } from "../api/endpoints";
import { PageHeader, DirectionalNote } from "../components/common";

const AGENT_ICON: Record<string, string> = {
  Router: "🧭",
  "SQL Generator": "🛠️",
  Retrieval: "🗄️",
  "Opportunity Engine": "💹",
  "Brand-Intel": "🏷️",
  "Knowledge (RAG)": "📚",
  Clarifier: "❓",
  Insight: "💡",
  Fallback: "🚧",
};

const INTENT_COLOR: Record<string, string> = {
  opportunity: "bg-violet-100 text-violet-700",
  brand_intel: "bg-blue-100 text-blue-700",
  data_query: "bg-green-100 text-green-700",
  clarify: "bg-amber-100 text-amber-700",
  out_of_scope: "bg-red-100 text-red-700",
};

const EXAMPLES = [
  "What are my best cross-match opportunities?",
  "Can I sell Maison Luxe?",
  "Why did a client push back on pricing?",
  "Any supplier emails about shipping delays?",
];

interface Turn {
  q: string;
  resp?: ChatResponse;
  loading?: boolean;
  error?: string;
}

export function AskAtlas() {
  const { auth } = useAuth();
  const region = auth!.activeRegion;
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);

  async function send(q: string) {
    if (!q.trim()) return;
    setInput("");
    const idx = turns.length;
    setTurns((t) => [...t, { q, loading: true }]);
    try {
      const resp = await askAtlas(q, region);
      setTurns((t) => t.map((tt, i) => (i === idx ? { q, resp } : tt)));
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.message || "Request failed";
      setTurns((t) => t.map((tt, i) => (i === idx ? { q, error: String(msg) } : tt)));
    }
  }

  return (
    <div className="max-w-4xl">
      <PageHeader
        title="🤖 Ask Atlas"
        subtitle="A LangGraph multi-agent system routes your question to the right specialist."
      />
      <DirectionalNote />

      <div className="flex flex-wrap gap-2 mb-4">
        {EXAMPLES.map((ex) => (
          <button key={ex} className="badge bg-slate-100 text-slate-600 hover:bg-brand-50" onClick={() => send(ex)}>
            {ex}
          </button>
        ))}
      </div>

      <div className="space-y-4 mb-6">
        {turns.map((t, i) => (
          <div key={i} className="space-y-2">
            <div className="flex justify-end">
              <div className="bg-brand-500 text-white rounded-2xl rounded-br-sm px-4 py-2 text-sm max-w-lg">
                {t.q}
              </div>
            </div>
            <div className="card p-4">
              {t.loading && (
                <div className="flex items-center gap-2 text-slate-500 text-sm">
                  <Loader2 className="animate-spin" size={16} /> Agents working…
                </div>
              )}
              {t.error && <div className="text-red-600 text-sm">{t.error}</div>}
              {t.resp && <ResponseView resp={t.resp} />}
            </div>
          </div>
        ))}
      </div>

      <form
        className="sticky bottom-0 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input
          className="flex-1 rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
          placeholder="Ask about opportunities, brands, deals, inventory…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="btn-primary" type="submit" disabled={!input.trim()}>
          <Send size={16} /> Ask
        </button>
      </form>
    </div>
  );
}

function ResponseView({ resp }: { resp: ChatResponse }) {
  const flow = resp.trace.map((s) => `${AGENT_ICON[s.agent] || "•"} ${s.agent}`).join("  →  ");
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        {resp.intent && (
          <span className={`badge ${INTENT_COLOR[resp.intent] || "bg-slate-100 text-slate-600"}`}>
            {resp.intent}
          </span>
        )}
        <span className="text-xs text-slate-400">{flow}</span>
      </div>

      {resp.error && <div className="text-amber-600 text-sm">{resp.error}</div>}
      <RichText text={resp.answer} />

      {resp.structured?.kind === "rag" && resp.structured.sources?.length > 0 && (
        <Sources sources={resp.structured.sources} />
      )}
      {resp.rows?.length > 0 && <RowsTable rows={resp.rows} />}

      <details className="text-xs">
        <summary className="cursor-pointer text-slate-400">Step-by-step trace</summary>
        <ol className="mt-2 space-y-1">
          {resp.trace.map((s, i) => (
            <li key={i} className="text-slate-600">
              <strong>{AGENT_ICON[s.agent] || "•"} {s.agent}</strong> — <em>{s.action}</em>
              {s.detail && <div className="text-slate-400 ml-4">{s.detail}</div>}
            </li>
          ))}
        </ol>
      </details>

      {resp.sql && (
        <details className="text-xs">
          <summary className="cursor-pointer text-slate-400">Generated SQL</summary>
          <pre className="mt-2 bg-slate-900 text-slate-100 rounded-lg p-3 overflow-auto">{resp.sql}</pre>
        </details>
      )}
    </div>
  );
}

// Lightweight renderer: **bold**, `code`, and preserved line breaks — enough for
// the agents' answers without pulling in a full markdown dependency.
function RichText({ text }: { text: string }) {
  const lines = (text || "").split("\n");
  return (
    <div className="text-slate-800 space-y-1">
      {lines.map((line, li) => (
        <p key={li}>
          {line.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((seg, i) => {
            if (seg.startsWith("**") && seg.endsWith("**"))
              return <strong key={i}>{seg.slice(2, -2)}</strong>;
            if (seg.startsWith("`") && seg.endsWith("`"))
              return (
                <code key={i} className="bg-slate-100 rounded px-1 text-[0.85em]">
                  {seg.slice(1, -1)}
                </code>
              );
            return <span key={i}>{seg}</span>;
          })}
        </p>
      ))}
    </div>
  );
}

function Sources({ sources }: { sources: any[] }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
      <div className="text-xs font-semibold text-slate-500 mb-2">📚 Retrieved sources</div>
      <ul className="space-y-1.5">
        {sources.map((s, i) => (
          <li key={i} className="text-xs">
            <span className="badge bg-white text-slate-500 mr-2">[{i + 1}]</span>
            <span className="font-medium text-slate-700">{s.title}</span>
            <span className="text-slate-400">
              {" "}· {s.type} · {s.region || "global"} · score {s.score}
            </span>
            <div className="text-slate-400 ml-8">{s.snippet}…</div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function RowsTable({ rows }: { rows: any[] }) {
  const cols = Object.keys(rows[0]);
  return (
    <div className="overflow-auto max-h-72 border border-slate-100 rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-500 text-xs sticky top-0">
          <tr>{cols.map((c) => <th key={c} className="px-3 py-2">{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.slice(0, 50).map((r, i) => (
            <tr key={i} className="border-t border-slate-100">
              {cols.map((c) => (
                <td key={c} className="px-3 py-1.5">{String(r[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
