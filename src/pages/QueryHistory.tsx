import { useState, useEffect } from "react";
import { Search, Download, RefreshCw, Filter, Loader2, History } from "lucide-react";
import { motion } from "motion/react";
import { apiFetch } from "../lib/api";

export default function QueryHistory() {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  async function fetchHistory() {
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/query/history?limit=50");
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.error("Failed to fetch history", e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Query History & Saved Responses</h1>
          <p className="text-sm text-slate-500">Review past compliance checks and AI interactions.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={fetchHistory} className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-slate-50 flex items-center gap-2 transition-colors">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden flex flex-col">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500 bg-slate-50">
              <tr>
                <th className="px-6 py-4 font-medium">Timestamp</th>
                <th className="px-6 py-4 font-medium">Query</th>
                <th className="px-6 py-4 font-medium">Citations</th>
                <th className="px-6 py-4 font-medium">Confidence</th>
                <th className="px-6 py-4 font-medium">Time</th>
                <th className="px-6 py-4 font-medium">Tokens</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-500" />
                    Loading history...
                  </td>
                </tr>
              ) : history.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-16 text-center">
                    <History className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-500 font-medium">No query history found</p>
                    <p className="text-sm text-slate-400 mt-1">Submit your first question in the Query Chat to see it here.</p>
                  </td>
                </tr>
              ) : (
                history.map((item, i) => (
                  <motion.tr
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    key={i}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-6 py-4 text-slate-600 whitespace-nowrap text-xs">{new Date(item.created_at).toLocaleString()}</td>
                    <td className="px-6 py-4">
                      <div className="max-w-xs truncate text-slate-900 font-medium">{item.query_text}</div>
                    </td>
                    <td className="px-6 py-4 text-slate-600">{(item.citations || []).length}</td>
                    <td className="px-6 py-4">
                      <span className={`font-mono text-xs font-bold ${item.confidence_score >= 0.7 ? 'text-emerald-600' :
                        item.confidence_score >= 0.4 ? 'text-amber-600' :
                          'text-rose-600'
                        }`}>
                        {(item.confidence_score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500 text-xs font-mono">{item.processing_time_ms}ms</td>
                    <td className="px-6 py-4 text-slate-500 text-xs font-mono">{item.tokens_used}</td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
