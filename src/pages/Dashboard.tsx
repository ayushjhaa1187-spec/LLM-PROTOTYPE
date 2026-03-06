import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { FileText, Activity, CheckCircle, DollarSign, UploadCloud, Play, Loader2, Database } from "lucide-react";
import { apiFetch } from "../lib/api";

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await apiFetch("/api/v1/admin/stats");
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      } else {
        setError("Failed to fetch dashboard metrics");
      }
    } catch (e) {
      console.error(e);
      setError("Network error occurred");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const kpis = stats ? [
    { label: "Total Documents", value: stats.total_documents, icon: FileText, color: "text-blue-600", bg: "bg-blue-100" },
    { label: "Total Queries", value: stats.total_queries, icon: Activity, color: "text-emerald-600", bg: "bg-emerald-100" },
    { label: "Avg Confidence", value: `${(stats.avg_confidence * 100).toFixed(1)}%`, icon: CheckCircle, color: "text-indigo-600", bg: "bg-indigo-100" },
    { label: "Est. Cost", value: `$${stats.estimated_cost}`, icon: DollarSign, color: "text-amber-600", bg: "bg-amber-100" },
    { label: "Vector Chunks", value: stats.vector_chunks, icon: Database, color: "text-violet-600", bg: "bg-violet-100" },
    { label: "Queries Today", value: stats.queries_today, icon: Activity, color: "text-rose-600", bg: "bg-rose-100" },
  ] : [];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-medium">Error:</span> {error}
          </div>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700">×</button>
        </div>
      )}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Dashboard Overview</h1>
          <p className="text-sm text-slate-500">Real-time platform metrics from your backend.</p>
        </div>
        <div className="flex gap-3">
          <Link to="/upload" className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium hover:bg-slate-50 flex items-center gap-2 transition-colors shadow-sm">
            <UploadCloud className="w-4 h-4" /> Upload
          </Link>
          <Link to="/chat" className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 flex items-center gap-2 transition-colors shadow-sm">
            <Play className="w-4 h-4" /> New Query
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {kpis.map((kpi, i) => {
          const Icon = kpi.icon;
          return (
            <div key={i} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4 hover:shadow-md hover:-translate-y-1 transition-all duration-200">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${kpi.bg} ${kpi.color}`}>
                <Icon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">{kpi.label}</p>
                <p className="text-2xl font-bold text-slate-900">{kpi.value}</p>
              </div>
            </div>
          );
        })}
      </div>

      {stats && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 text-slate-900">System Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="p-4 bg-slate-50 rounded-lg">
              <div className="text-slate-500 mb-1">Users</div>
              <div className="text-xl font-bold text-slate-900">{stats.total_users}</div>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <div className="text-slate-500 mb-1">Total Tokens</div>
              <div className="text-xl font-bold text-slate-900">{stats.total_tokens?.toLocaleString() || 0}</div>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <div className="text-slate-500 mb-1">Avg Response</div>
              <div className="text-xl font-bold text-slate-900">{stats.avg_response_time_ms}ms</div>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <div className="text-slate-500 mb-1">Vector Chunks</div>
              <div className="text-xl font-bold text-slate-900">{stats.vector_chunks}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
