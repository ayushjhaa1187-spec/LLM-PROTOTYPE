import { useState, useEffect } from "react";
import { FileText, CheckCircle, Loader2, AlertCircle, RefreshCw, Trash2, HardDrive } from "lucide-react";
import { motion } from "motion/react";
import { apiFetch } from "../lib/api";

type DocStatus = {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  chunk_count: number;
  error_message: string | null;
  created_at: string;
};

export default function DocumentStatus() {
  const [docs, setDocs] = useState<DocStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocs = async () => {
    try {
      const res = await apiFetch("/api/v1/documents/status");
      if (res.ok) {
        const data = await res.json();
        setDocs(data);
        setError(null);
      } else {
        setError("Failed to fetch documents status");
      }
    } catch (e) {
      console.error("Failed to fetch document status", e);
      setError("Network error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this document?")) return;
    try {
      const res = await apiFetch(`/api/v1/documents/${id}`, { method: "DELETE" });
      if (res.ok) {
        setDocs(docs => docs.filter(d => d.id !== id));
      } else {
        alert("Failed to delete document");
      }
    } catch (e) {
      console.error(e);
      alert("Error deleting document");
    }
  };

  useEffect(() => {
    fetchDocs();
    // Poll every 3 seconds for status updates
    const interval = setInterval(fetchDocs, 3000);
    return () => clearInterval(interval);
  }, []);

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle className="w-5 h-5 text-emerald-500" />;
      case "processing": return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case "failed": return <AlertCircle className="w-5 h-5 text-rose-500" />;
      default: return <FileText className="w-5 h-5 text-slate-400" />;
    }
  };

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      uploaded: "bg-slate-100 text-slate-800",
      processing: "bg-blue-100 text-blue-800",
      completed: "bg-emerald-100 text-emerald-800",
      failed: "bg-rose-100 text-rose-800",
    };
    return colors[status] || "bg-slate-100 text-slate-800";
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Processing Status</h1>
          <p className="text-sm text-slate-500">Track document ingestion progress. Auto-refreshes every 3s.</p>
        </div>
        <button onClick={fetchDocs} className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-slate-50 flex items-center gap-2 transition-colors">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            <span className="font-medium">Error:</span> {error}
          </div>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700">×</button>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-3" />
            <p className="text-slate-500">Loading document status...</p>
          </div>
        ) : docs.length === 0 ? (
          <div className="p-16 text-center text-slate-500 flex flex-col items-center">
            <HardDrive className="w-12 h-12 text-slate-300 mb-4" />
            <p className="text-slate-500 font-medium">No documents indexed</p>
            <p className="text-sm text-slate-400 mt-1">Go to Upload Documents to start building your Vector Engine knowledge base.</p>
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500 bg-slate-50">
              <tr>
                <th className="px-6 py-4 font-medium">Document</th>
                <th className="px-6 py-4 font-medium">Type</th>
                <th className="px-6 py-4 font-medium">Size</th>
                <th className="px-6 py-4 font-medium">Chunks</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Uploaded</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {docs.map((doc, i) => (
                <motion.tr
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  key={doc.id}
                  className="hover:bg-slate-50 transition-colors"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      {statusIcon(doc.status)}
                      <span className="font-medium text-slate-900">{doc.filename}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 uppercase text-xs font-bold text-slate-500">{doc.file_type}</td>
                  <td className="px-6 py-4 text-slate-600">{(doc.file_size / 1024).toFixed(0)} KB</td>
                  <td className="px-6 py-4 text-slate-600">{doc.chunk_count || "—"}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${statusBadge(doc.status)}`}>
                      {doc.status}
                    </span>
                    {doc.error_message && (
                      <p className="text-xs text-rose-500 mt-1">{doc.error_message}</p>
                    )}
                  </td>
                  <td className="px-6 py-4 text-slate-500 text-xs">{new Date(doc.created_at).toLocaleString()}</td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="text-rose-500 hover:text-rose-700 p-2 rounded-lg hover:bg-rose-50 transition-colors"
                      title="Delete Document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
