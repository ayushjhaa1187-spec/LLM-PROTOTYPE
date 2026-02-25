import { useState } from "react";
import { UploadCloud, FileText, X, Play } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function UploadDocuments() {
  const [files, setFiles] = useState<{ name: string; size: string }[]>([]);
  const navigate = useNavigate();

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files).map(f => ({
      name: f.name,
      size: (f.size / 1024 / 1024).toFixed(2) + " MB"
    }));
    setFiles([...files, ...droppedFiles]);
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleStartProcessing = () => {
    navigate("/documents/status");
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Upload Documents</h1>
        <p className="text-sm text-slate-500">Ingest PDFs, DOCX, TXT, or ZIP files for processing.</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <div 
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-slate-300 rounded-xl p-12 flex flex-col items-center justify-center bg-slate-50 hover:bg-blue-50 hover:border-blue-300 transition-colors cursor-pointer"
          >
            <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-4">
              <UploadCloud className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-1">Drag & Drop files here</h3>
            <p className="text-sm text-slate-500 mb-4">or click to browse from your computer</p>
            <button className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-slate-50">
              Select Files
            </button>
          </div>

          {files.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 bg-slate-50 font-medium text-slate-700">
                Selected Files ({files.length})
              </div>
              <ul className="divide-y divide-slate-100">
                {files.map((file, i) => (
                  <li key={i} className="px-4 py-3 flex items-center justify-between hover:bg-slate-50">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-blue-500" />
                      <div>
                        <p className="text-sm font-medium text-slate-900">{file.name}</p>
                        <p className="text-xs text-slate-500">{file.size}</p>
                      </div>
                    </div>
                    <button onClick={() => removeFile(i)} className="text-slate-400 hover:text-rose-500 p-1">
                      <X className="w-4 h-4" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6 h-fit">
          <h3 className="font-semibold text-slate-900 mb-4">Processing Options</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Document Type</label>
              <select className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                <option>Regulation (FAR/DFARS)</option>
                <option>RFP / Solicitation</option>
                <option>Internal Policy</option>
                <option>Other</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Tags (Comma separated)</label>
              <input type="text" placeholder="e.g., cyber, compliance, 2026" className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Access Rules</label>
              <select className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                <option>Public (Workspace)</option>
                <option>Private (Only Me)</option>
                <option>Restricted (Admins Only)</option>
              </select>
            </div>

            <div className="pt-4 border-t border-slate-100">
              <button 
                onClick={handleStartProcessing}
                disabled={files.length === 0}
                className="w-full bg-blue-600 text-white rounded-lg py-2.5 font-medium flex items-center justify-center gap-2 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Play className="w-4 h-4" /> Start Processing
              </button>
              <button className="w-full mt-2 bg-slate-100 text-slate-700 rounded-lg py-2.5 font-medium text-sm hover:bg-slate-200 transition-colors">
                Load Demo Dataset
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
