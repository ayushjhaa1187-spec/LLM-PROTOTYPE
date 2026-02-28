import { useState, useEffect } from "react";
import { Activity, Server, AlertTriangle, DollarSign, RefreshCw, Loader2 } from "lucide-react";
import { apiFetch } from "../lib/api";

export default function AdminDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, logsRes] = await Promise.all([
        apiFetch("/api/v1/admin/stats"),
        apiFetch("/api/v1/admin/audit-logs?limit=20"),
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (logsRes.ok) setAuditLogs(await logsRes.json());
    } catch (e) {
      console.error(e);
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

  const statCards = stats ? [
    { label: "Total Users", value: stats.total_users, icon: Server, color: "text-blue-600", bg: "bg-blue-100" },
    { label: "Queries Today", value: stats.queries_today, icon: Activity, color: "text-emerald-600", bg: "bg-emerald-100" },
    { label: "Total Queries", value: stats.total_queries, icon: Activity, color: "text-indigo-600", bg: "bg-indigo-100" },
    { label: "Est. Token Cost", value: `$${stats.estimated_cost}`, icon: DollarSign, color: "text-amber-600", bg: "bg-amber-100" },
  ] : [];

  return (
    <div className="max-w-6xl mx-auto space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">System Dashboard</h1>
          <p className="text-sm text-slate-500">Live platform health and audit logs from the backend.</p>
        </div>
        <button onClick={fetchData} className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-slate-50 flex items-center gap-2 transition-colors">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div key={i} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${stat.bg} ${stat.color}`}>
                <Icon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">{stat.label}</p>
                <p className="text-2xl font-bold text-slate-900">{stat.value}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 text-slate-900">System Metrics</h2>
          {stats && (
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 border border-slate-100 rounded-lg bg-slate-50">
                <p className="text-sm text-slate-500 mb-1">Total Documents</p>
                <p className="text-xl font-bold text-slate-900">{stats.total_documents}</p>
              </div>
              <div className="p-4 border border-slate-100 rounded-lg bg-slate-50">
                <p className="text-sm text-slate-500 mb-1">Vector Chunks</p>
                <p className="text-xl font-bold text-slate-900">{stats.vector_chunks}</p>
              </div>
              <div className="p-4 border border-slate-100 rounded-lg bg-slate-50">
                <p className="text-sm text-slate-500 mb-1">Avg Confidence</p>
                <p className="text-xl font-bold text-slate-900">{(stats.avg_confidence * 100).toFixed(1)}%</p>
              </div>
              <div className="p-4 border border-slate-100 rounded-lg bg-slate-50">
                <p className="text-sm text-slate-500 mb-1">Avg Response Time</p>
                <p className="text-xl font-bold text-slate-900">{stats.avg_response_time_ms}ms</p>
              </div>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 text-slate-900">Recent Audit Logs</h2>
          <div className="space-y-4 max-h-80 overflow-y-auto">
            {auditLogs.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No audit logs yet.</p>
            ) : (
              auditLogs.map((log) => (
                <div key={log.id} className="flex gap-3">
                  <div className="mt-1">
                    <div className={`w-2 h-2 rounded-full ${log.action.includes('FAIL') || log.action.includes('ERROR') ? 'bg-rose-500' :
                        log.action.includes('LOGIN') || log.action.includes('REGISTER') ? 'bg-blue-500' :
                          'bg-slate-400'
                      }`} />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">{log.action}</p>
                    <p className="text-xs text-slate-500 truncate max-w-[200px]">{log.detail || log.resource || "—"}</p>
                    <p className="text-xs text-slate-400 mt-1">{new Date(log.timestamp).toLocaleString()}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
