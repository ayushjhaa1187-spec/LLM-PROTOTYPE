import { useState, useEffect } from "react";
import { CheckCircle, Circle, Clock, Search, Edit3, ShieldCheck, BarChart3, Loader2 } from "lucide-react";
import { apiFetch } from "../lib/api";

type StepLog = {
  step: string;
  name: string;
  status: string;
  time_ms: number;
  logs: string[];
  output?: any;
};

export default function AgentSteps() {
  const [steps, setSteps] = useState<StepLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [queryText, setQueryText] = useState("");

  useEffect(() => {
    fetchLatestPipeline();
  }, []);

  const fetchLatestPipeline = async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/query/history?limit=1");
      if (!res.ok) { setLoading(false); return; }
      const history = await res.json();
      if (history.length === 0) { setLoading(false); return; }

      const latest = history[0];
      setQueryText(latest.query_text);
      setSteps(latest.agent_logs || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const stepIcons: Record<string, any> = {
    research: Search,
    draft: Edit3,
    verify: ShieldCheck,
    score: BarChart3,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 font-sans">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Agent Reasoning Steps</h1>
        <p className="text-sm text-slate-500">Real execution trace from the multi-agent RAG pipeline.</p>
        {queryText && <p className="text-xs text-blue-600 mt-1">Query: "{queryText}"</p>}
      </div>

      {steps.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-12 text-center text-slate-500">
          No pipeline data yet. Run a query in Query Chat first.
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-8">
          <div className="space-y-8">
            {steps.map((step, index) => {
              const Icon = stepIcons[step.step] || Circle;
              const isLast = index === steps.length - 1;
              return (
                <div key={index} className="relative flex gap-6">
                  {!isLast && (
                    <div className={`absolute left-6 top-10 bottom-[-2rem] w-0.5 ${step.status === 'completed' ? 'bg-emerald-500' : 'bg-slate-200'}`} />
                  )}
                  <div className="relative z-10 flex-shrink-0">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center border-2 ${step.status === 'completed' ? 'bg-emerald-100 border-emerald-500 text-emerald-600' :
                        step.status === 'skipped' ? 'bg-slate-50 border-slate-300 text-slate-400' :
                          'bg-blue-100 border-blue-500 text-blue-600'
                      }`}>
                      <Icon className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="flex-1 pt-2">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="text-lg font-bold text-slate-900">{step.name}</h3>
                      <span className="text-xs font-mono text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" /> {step.time_ms}ms
                      </span>
                    </div>
                    <div className="space-y-2 mt-3">
                      {(step.logs || []).map((log, i) => (
                        <div key={i} className="text-sm text-slate-600 bg-slate-50 border border-slate-100 p-2 rounded-md font-mono text-xs flex items-start gap-2">
                          <span className="text-blue-500 mt-0.5">&gt;</span>
                          <span className="break-all">{log}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
