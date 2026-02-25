import { Link } from "react-router-dom";
import { FileText, CheckCircle, AlertCircle, Clock, RefreshCw } from "lucide-react";

export default function DocumentStatus() {
  const documents = [
    { id: "1", name: "FAR_Part_19_Small_Business.pdf", size: "2.4 MB", status: "completed", progress: 100, step: "Indexed" },
    { id: "2", name: "DoD_Cloud_SRG_v1.docx", size: "1.1 MB", status: "processing", progress: 65, step: "Extracting Entities" },
    { id: "3", name: "NIST_SP_800_171.pdf", size: "5.8 MB", status: "queued", progress: 0, step: "Waiting" },
    { id: "4", name: "Legacy_Contract_Scrape.txt", size: "0.5 MB", status: "failed", progress: 45, step: "Noise Filtering Failed" },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Processing Status</h1>
          <p className="text-sm text-slate-500">Live status of document ingestion pipelines.</p>
        </div>
        <button className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-slate-50 flex items-center gap-2 transition-colors">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-500">
            <tr>
              <th className="px-6 py-4 font-medium">Document</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium">Progress</th>
              <th className="px-6 py-4 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {documents.map((doc) => (
              <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <FileText className={`w-5 h-5 ${doc.status === 'failed' ? 'text-rose-500' : 'text-blue-500'}`} />
                    <div>
                      <Link to={`/documents/${doc.id}`} className="font-medium text-slate-900 hover:text-blue-600 transition-colors">
                        {doc.name}
                      </Link>
                      <p className="text-xs text-slate-500">{doc.size}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    {doc.status === "completed" && <CheckCircle className="w-4 h-4 text-emerald-500" />}
                    {doc.status === "processing" && <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />}
                    {doc.status === "queued" && <Clock className="w-4 h-4 text-slate-400" />}
                    {doc.status === "failed" && <AlertCircle className="w-4 h-4 text-rose-500" />}
                    <span className={`font-medium capitalize ${
                      doc.status === 'completed' ? 'text-emerald-700' :
                      doc.status === 'processing' ? 'text-blue-700' :
                      doc.status === 'failed' ? 'text-rose-700' : 'text-slate-600'
                    }`}>
                      {doc.status}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${
                          doc.status === 'completed' ? 'bg-emerald-500' :
                          doc.status === 'failed' ? 'bg-rose-500' : 'bg-blue-500'
                        }`} 
                        style={{ width: `${doc.progress}%` }}
                      ></div>
                    </div>
                    <span className="text-xs font-medium text-slate-600 min-w-[3ch]">{doc.progress}%</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{doc.step}</p>
                </td>
                <td className="px-6 py-4 text-right">
                  {doc.status === "failed" ? (
                    <button className="text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors">Retry</button>
                  ) : doc.status === "completed" ? (
                    <Link to={`/documents/${doc.id}`} className="text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors">View</Link>
                  ) : (
                    <button className="text-sm font-medium text-slate-400 hover:text-slate-600 transition-colors">Logs</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
