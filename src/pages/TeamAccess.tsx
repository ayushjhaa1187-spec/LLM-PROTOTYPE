import { useState, useEffect } from "react";
import { Users, Shield, UserPlus, Settings, Loader2 } from "lucide-react";
import { apiFetch, getUser } from "../lib/api";

export default function TeamAccess() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const currentUser = getUser();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/admin/users");
      if (res.ok) {
        setUsers(await res.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const updateRole = async (userId: string, newRole: string) => {
    setErrorMsg("");
    try {
      const res = await apiFetch(`/api/v1/admin/users/${userId}`, {
        method: "PUT",
        body: JSON.stringify({ role: newRole }),
      });
      if (res.ok) {
        fetchUsers();
      } else {
        const data = await res.json();
        setErrorMsg(data.detail || "Failed to update role");
      }
    } catch (e: any) {
      setErrorMsg(e.message || "Network error");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Team & Access Control</h1>
          <p className="text-sm text-slate-500">Manage users and roles from the live database.</p>
        </div>
      </div>

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-lg text-sm">
          {errorMsg}
        </div>
      )}

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
              {users.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-slate-500">No users found.</td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900">{user.full_name}</div>
                      <div className="text-xs text-slate-500">{user.email}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${user.role === 'admin' ? 'bg-indigo-100 text-indigo-800' :
                        user.role === 'analyst' ? 'bg-blue-100 text-blue-800' :
                          'bg-slate-100 text-slate-800'
                        }`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`flex items-center gap-1.5 text-xs font-medium ${user.is_active ? 'text-emerald-600' : 'text-rose-600'
                        }`}>
                        <div className={`w-1.5 h-1.5 rounded-full ${user.is_active ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                        {user.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {currentUser?.role === 'admin' && user.id !== currentUser?.id && (
                        <select
                          value={user.role}
                          onChange={(e) => updateRole(user.id, e.target.value)}
                          className="text-xs border border-slate-200 rounded-lg px-2 py-1 focus:ring-2 focus:ring-blue-500 outline-none"
                        >
                          <option value="admin">Admin</option>
                          <option value="analyst">Analyst</option>
                          <option value="viewer">Viewer</option>
                        </select>
                      )}
                    </td>
                  </tr>
                ))
              )}
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
              <h3 className="text-sm font-bold text-slate-800 mb-1">Role Permissions</h3>
              <p className="text-xs text-slate-500 mb-3">Current role hierarchy.</p>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between"><span className="font-medium">Admin</span><span className="text-slate-500">Full access</span></div>
                <div className="flex justify-between"><span className="font-medium">Analyst</span><span className="text-slate-500">Query + Upload</span></div>
                <div className="flex justify-between"><span className="font-medium">Viewer</span><span className="text-slate-500">Read only</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
