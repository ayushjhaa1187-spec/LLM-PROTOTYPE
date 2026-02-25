import { Link } from "react-router-dom";
import { FileText, Activity, CheckCircle, DollarSign, UploadCloud, Play } from "lucide-react";

export default function Dashboard() {
  const kpis = [
    { label: "Total BRDs", value: "142", icon: FileText, color: "text-blue-600", bg: "bg-blue-100" },
    { label: "Active Pipelines", value: "3", icon: Activity, color: "text-emerald-600", bg: "bg-emerald-100" },
    { label: "Avg Accuracy", value: "98.2%", icon: CheckCircle, color: "text-indigo-600", bg: "bg-indigo-100" },
    { label: "Token Cost (MTD)", value: "$42.50", icon: DollarSign, color: "text-amber-600", bg: "bg-amber-100" },
  ];

  const recentActivity = [
    { id: 1, action: "Pipeline completed", target: "FAR Part 15 Update", time: "10 mins ago", status: "success" },
    { id: 2, action: "Document uploaded", target: "DoD Cloud Security SRG", time: "1 hour ago", status: "info" },
    { id: 3, action: "Query run", target: "Set-aside eligibility for NAICS 541511", time: "2 hours ago", status: "info" },
    { id: 4, action: "Pipeline failed", target: "Legacy Contract Scrape", time: "5 hours ago", status: "error" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Dashboard Overview</h1>
          <p className="text-sm text-slate-500">Welcome back. Here's what's happening today.</p>
        </div>
        <div className="flex gap-3">
          <Link to="/upload" className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium hover:bg-slate-50 flex items-center gap-2 transition-colors shadow-sm">
            <UploadCloud className="w-4 h-4" /> Quick Upload
          </Link>
          <Link to="/chat" className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 flex items-center gap-2 transition-colors shadow-sm">
            <Play className="w-4 h-4" /> New Query
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, i) => {
          const Icon = kpi.icon;
          return (
            <div key={i} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 text-slate-900">Active Pipelines</h2>
          <div className="space-y-4">
            <div className="p-4 border border-slate-100 rounded-lg bg-slate-50 flex items-center justify-between">
              <div>
                <h3 className="font-medium text-slate-900">Ingest: NIST SP 800-53 Rev 5</h3>
                <p className="text-sm text-slate-500">Extracting entities and chunking...</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 w-[45%]"></div>
                </div>
                <span className="text-sm font-medium text-slate-600">45%</span>
              </div>
            </div>
            <div className="p-4 border border-slate-100 rounded-lg bg-slate-50 flex items-center justify-between">
              <div>
                <h3 className="font-medium text-slate-900">Reindex: ChromaDB Main</h3>
                <p className="text-sm text-slate-500">Generating embeddings...</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-500 w-[82%]"></div>
                </div>
                <span className="text-sm font-medium text-slate-600">82%</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 text-slate-900">Recent Activity</h2>
          <div className="space-y-4">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="flex gap-3">
                <div className="mt-1">
                  <div className={\`w-2 h-2 rounded-full \${
                    activity.status === 'success' ? 'bg-emerald-500' :
                    activity.status === 'error' ? 'bg-rose-500' : 'bg-blue-500'
                  }\`}></div>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-900">{activity.action}</p>
                  <p className="text-xs text-slate-500 truncate max-w-[200px]">{activity.target}</p>
                  <p className="text-xs text-slate-400 mt-1">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
