import { Users, Shield, UserPlus, Settings } from "lucide-react";

export default function TeamAccess() {
  const users = [
    { id: 1, name: "Jane Doe", email: "jane@example.com", role: "Admin", status: "Active" },
    { id: 2, name: "John Smith", email: "john@example.com", role: "Editor", status: "Active" },
    { id: 3, name: "Alice Johnson", email: "alice@example.com", role: "Viewer", status: "Pending" },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Team & Access Control</h1>
          <p className="text-sm text-slate-500">Manage users, roles, and document access rules.</p>
        </div>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-blue-700 flex items-center gap-2 transition-colors">
          <UserPlus className="w-4 h-4" /> Invite User
        </button>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
            <h2 className="font-semibold text-slate-800 flex items-center gap-2"><Users className="w-5 h-5 text-blue-500" /> Workspace Members</h2>
          </div>
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500 bg-white">
              <tr>
                <th className="px-6 py-4 font-medium">User</th>
                <th className="px-6 py-4 font-medium">Role</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-900">{user.name}</div>
                    <div className="text-xs text-slate-500">{user.email}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                      user.role === 'Admin' ? 'bg-indigo-100 text-indigo-800' :
                      user.role === 'Editor' ? 'bg-blue-100 text-blue-800' :
                      'bg-slate-100 text-slate-800'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`flex items-center gap-1.5 text-xs font-medium ${
                      user.status === 'Active' ? 'text-emerald-600' : 'text-amber-600'
                    }`}>
                      <div className={`w-1.5 h-1.5 rounded-full ${user.status === 'Active' ? 'bg-emerald-500' : 'bg-amber-500'}`}></div>
                      {user.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-slate-400 hover:text-blue-600 transition-colors p-1">
                      <Settings className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
            <h2 className="font-semibold text-slate-800 flex items-center gap-2"><Shield className="w-5 h-5 text-emerald-500" /> Access Rules</h2>
          </div>
          <div className="p-6 space-y-4 flex-1">
            <div className="p-4 border border-slate-200 rounded-lg bg-slate-50">
              <h3 className="text-sm font-bold text-slate-800 mb-1">Default Document Policy</h3>
              <p className="text-xs text-slate-500 mb-3">Applies to newly uploaded documents.</p>
              <select className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white">
                <option>Workspace Public</option>
                <option>Private to Uploader</option>
                <option>Admins Only</option>
              </select>
            </div>
            
            <div className="p-4 border border-slate-200 rounded-lg bg-slate-50">
              <h3 className="text-sm font-bold text-slate-800 mb-1">Clearance Levels</h3>
              <p className="text-xs text-slate-500 mb-3">Require specific clearance tags for access.</p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-rose-100 text-rose-800 text-xs font-bold rounded uppercase tracking-wider">Top Secret</span>
                <span className="px-2 py-1 bg-amber-100 text-amber-800 text-xs font-bold rounded uppercase tracking-wider">Secret</span>
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-bold rounded uppercase tracking-wider">CUI</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
