import { Link } from "react-router-dom";
import { Briefcase, Plus, Settings } from "lucide-react";

export default function WorkspaceSelector() {
  const workspaces = [
    { id: "1", name: "Acme Corp Gov", brds: 12, pipelines: 2, role: "Admin" },
    { id: "2", name: "Defense Solutions LLC", brds: 45, pipelines: 5, role: "Member" },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center py-20 font-sans text-slate-900">
      <div className="w-full max-w-3xl px-6">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold tracking-tight mb-2">Select a Workspace</h1>
          <p className="text-slate-500">Choose an organization to continue.</p>
        </div>

        <div className="grid gap-4">
          {workspaces.map((ws) => (
            <Link
              key={ws.id}
              to="/dashboard"
              className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-md hover:border-blue-300 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center">
                  <Briefcase className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold group-hover:text-blue-600 transition-colors">{ws.name}</h2>
                  <p className="text-sm text-slate-500">
                    {ws.brds} BRDs • {ws.pipelines} Active Pipelines
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="px-2.5 py-1 bg-slate-100 text-slate-600 text-xs font-medium rounded-full">
                  {ws.role}
                </span>
                <Settings className="w-5 h-5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </Link>
          ))}

          <button className="border-2 border-dashed border-slate-300 bg-transparent p-6 rounded-xl text-slate-500 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50 transition-all flex items-center justify-center gap-2 font-medium">
            <Plus className="w-5 h-5" />
            Create New Workspace
          </button>
        </div>
      </div>
    </div>
  );
}
