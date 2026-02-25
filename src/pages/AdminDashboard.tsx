import { Activity, Server, AlertTriangle, Cpu, DollarSign } from "lucide-react";

export default function AdminDashboard() {
  const stats = [
    { label: "Worker Queue Depth", value: "12", icon: Server, color: "text-blue-600", bg: "bg-blue-100" },
    { label: "Active Celery Tasks", value: "4", icon: Activity, color: "text-emerald-600", bg: "bg-emerald-100" },
    { label: "Top Errors (24h)", value: "3", icon: AlertTriangle, color: "text-rose-600", bg: "bg-rose-100" },
    { label: "Est. Token Cost", value: "$425.50", icon: DollarSign, color: "text-amber-600", bg: "bg-amber-100" },
  ];

  const auditLogs = [
    { id: 1, action: "User Login", user: "jane@example.com", ip: "192.168.1.1", time: "10 mins ago" },
    { id: 2, action: "Document Uploaded", user: "john@example.com", ip: "10.0.0.5", time: "1 hour ago" },
    { id: 3, action: "Access Rule Changed", user: "admin@example.com", ip: "172.16.0.2", time: "2 hours ago" },
    { id: 4, action: "Failed Login Attempt", user: "unknown", ip: "203.0.113.42", time: "5 hours ago" },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">System Dashboard</h1>
          <p className="text-sm text-slate-500">Monitor platform health, queue stats, and audit logs.</p>
        </div>
        <div className="flex gap-3">
          <button className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-slate-50 flex items-center gap-2 transition-colors">
            <Cpu className="w-4 h-4" /> Restart Workers
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div key={i} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
              <div className={\`w-12 h-12 rounded-lg flex items-center justify-center \${stat.bg} \${stat.color}\`}>
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
          <h2 className="text-lg font-semibold mb-4 text-slate-900">System Health & Queues</h2>
          <div className="space-y-4">
            <div className="p-4 border border-slate-100 rounded-lg bg-slate-50 flex items-center justify-between">
              <div>
                <h3 className="font-medium text-slate-900">Celery Worker 1 (Ingestion)</h3>
                <p className="text-sm text-slate-500">Status: Healthy • CPU: 45% • Mem: 1.2GB</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-emerald-500 rounded-full"></div>
              </div>
            </div>
            <div className="p-4 border border-slate-100 rounded-lg bg-slate-50 flex items-center justify-between">
              <div>
                <h3 className="font-medium text-slate-900">Celery Worker 2 (Generation)</h3>
                <p className="text-sm text-slate-500">Status: High Load • CPU: 92% • Mem: 3.8GB</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-amber-500 rounded-full animate-pulse"></div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 text-slate-900">Recent Audit Logs</h2>
          <div className="space-y-4">
            {auditLogs.map((log) => (
              <div key={log.id} className="flex gap-3">
                <div className="mt-1">
                  <div className={\`w-2 h-2 rounded-full \${
                    log.action.includes('Failed') ? 'bg-rose-500' : 'bg-slate-400'
                  }\`}></div>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-900">{log.action}</p>
                  <p className="text-xs text-slate-500 truncate max-w-[200px]">{log.user} ({log.ip})</p>
                  <p className="text-xs text-slate-400 mt-1">{log.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
