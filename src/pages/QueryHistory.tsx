import { useState, useEffect } from "react";
import { Search, Download, RefreshCw, Filter } from "lucide-react";

export default function QueryHistory() {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const res = await fetch("/api/v1/history");
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
    fetchHistory();
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Query History & Saved Responses</h1>
          <p className="text-sm text-slate-500">Review past compliance checks and AI interactions.</p>
        </div>
        <div className="flex gap-3">
          <button className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-slate-50 flex items-center gap-2 transition-colors">
            <Download className="w-4 h-4" /> Export CSV
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input type="text" placeholder="Search queries..." className="pl-9 pr-4 py-2 w-full border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
          </div>
          <button className="bg-white border border-slate-200 text-slate-700 px-3 py-2 rounded-lg text-sm font-medium shadow-sm hover:bg-slate-50 flex items-center gap-2 transition-colors">
            <Filter className="w-4 h-4" /> Filters
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500 bg-white">
              <tr>
                <th className="px-6 py-4 font-medium">Timestamp</th>
                <th className="px-6 py-4 font-medium">Workflow</th>
                <th className="px-6 py-4 font-medium">Query Parameters</th>
                <th className="px-6 py-4 font-medium">Risk Level</th>
                <th className="px-6 py-4 font-medium">Confidence</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-500" />
                    Loading history...
                  </td>
                </tr>
              ) : history.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500">No history found.</td>
                </tr>
              ) : (
                history.map((item, i) => {
                  const params = JSON.parse(item.query_params);
                  return (
                    <tr key={i} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4 text-slate-600 whitespace-nowrap">{new Date(item.timestamp).toLocaleString()}</td>
                      <td className="px-6 py-4 font-medium text-slate-900 capitalize">{item.workflow}</td>
                      <td className="px-6 py-4">
                        <div className="max-w-xs truncate text-xs font-mono text-slate-500">
                          {Object.entries(params).map(([k, v]) => `${k}: ${v}`).join(', ')}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                          item.risk_level === 'low' ? 'bg-emerald-100 text-emerald-800' : 
                          item.risk_level === 'medium' ? 'bg-amber-100 text-amber-800' : 
                          'bg-rose-100 text-rose-800'
                        }`}>
                          {item.risk_level}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono text-xs font-bold text-blue-600">
                        {(item.confidence * 100).toFixed(0)}%
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button className="text-blue-600 hover:text-blue-800 font-medium text-sm transition-colors">View</button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
