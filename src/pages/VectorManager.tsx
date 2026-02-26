import { Database, Plus, RefreshCw, Settings } from "lucide-react";

export default function VectorManager() {
  const indices = [
    { name: "far-regulations-prod", db: "Pinecone", docs: 12450, size: "4.2 GB", updated: "2 hours ago", status: "active" },
    { name: "dfars-dev", db: "ChromaDB", docs: 320, size: "150 MB", updated: "1 day ago", status: "active" },
    { name: "internal-policies", db: "Pinecone", docs: 85, size: "45 MB", updated: "5 days ago", status: "indexing" },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Vector Index Manager</h1>
          <p className="text-sm text-slate-500">Manage vector databases, namespaces, and re-indexing tasks.</p>
        </div>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-blue-700 flex items-center gap-2 transition-colors">
          <Plus className="w-4 h-4" /> Create Index
        </button>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg flex items-center justify-center bg-blue-100 text-blue-600">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Total Documents</p>
            <p className="text-2xl font-bold text-slate-900">12,855</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg flex items-center justify-center bg-emerald-100 text-emerald-600">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Total Size</p>
            <p className="text-2xl font-bold text-slate-900">4.4 GB</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg flex items-center justify-center bg-amber-100 text-amber-600">
            <RefreshCw className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Active Re-indexes</p>
            <p className="text-2xl font-bold text-slate-900">1</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
          <h2 className="font-semibold text-slate-800">Active Indices</h2>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-slate-500">
            <tr>
              <th className="px-6 py-4 font-medium">Index Name</th>
              <th className="px-6 py-4 font-medium">Database</th>
              <th className="px-6 py-4 font-medium">Documents</th>
              <th className="px-6 py-4 font-medium">Size</th>
              <th className="px-6 py-4 font-medium">Last Updated</th>
              <th className="px-6 py-4 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {indices.map((idx, i) => (
              <tr key={i} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${idx.status === 'active' ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`}></div>
                    <span className="font-medium text-slate-900">{idx.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${idx.db === 'Pinecone' ? 'bg-indigo-100 text-indigo-800' : 'bg-blue-100 text-blue-800'}`}>
                    {idx.db}
                  </span>
                </td>
                <td className="px-6 py-4 text-slate-600">{idx.docs.toLocaleString()}</td>
                <td className="px-6 py-4 text-slate-600">{idx.size}</td>
                <td className="px-6 py-4 text-slate-500">{idx.updated}</td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-3">
                    <button className="text-slate-400 hover:text-blue-600 transition-colors" title="Reindex">
                      <RefreshCw className={`w-4 h-4 ${idx.status === 'indexing' ? 'animate-spin text-blue-500' : ''}`} />
                    </button>
                    <button className="text-slate-400 hover:text-slate-800 transition-colors" title="Settings">
                      <Settings className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
