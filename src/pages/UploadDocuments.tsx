import React, { useState } from "react";
import { UploadCloud, FileText, X, Play, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../lib/api";

type FileEntry = {
  file: File;
  name: string;
  size: string;
  status: "pending" | "uploading" | "done" | "error";
  error?: string;
};

export default function UploadDocuments() {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [uploading, setUploading] = useState(false);
  const [tags, setTags] = useState("");
  const [docType, setDocType] = useState("Regulation (FAR/DFARS)");
  const navigate = useNavigate();

  const addFiles = (fileList: FileList | File[]) => {
    const newFiles: FileEntry[] = Array.from(fileList).map(f => ({
      file: f,
      name: f.name,
      size: (f.size / 1024 / 1024).toFixed(2) + " MB",
      status: "pending" as const,
    }));
    setFiles(prev => [...prev, ...newFiles]);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    addFiles(e.dataTransfer.files);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) addFiles(e.target.files);
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleStartProcessing = async () => {
    setUploading(true);

    for (let i = 0; i < files.length; i++) {
      const entry = files[i];
      if (entry.status === "done") continue;

      setFiles(prev => prev.map((f, idx) =>
        idx === i ? { ...f, status: "uploading" } : f
      ));

      try {
        const formData = new FormData();
        formData.append("file", entry.file);

        // combine doctype and tags
        const allTags = [docType, ...tags.split(",").filter(t => t.trim() !== "")].join(",");
        formData.append("tags", allTags);
        formData.append("access_level", "public");

        const res = await apiFetch("/api/v1/documents/upload", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || "Upload failed");
        }

        setFiles(prev => prev.map((f, idx) =>
          idx === i ? { ...f, status: "done" } : f
        ));
      } catch (err: any) {
        setFiles(prev => prev.map((f, idx) =>
          idx === i ? { ...f, status: "error", error: err.message } : f
        ));
      }
    }

    setUploading(false);
    // Navigate to status page after a short delay
    setTimeout(() => navigate("/documents/status"), 1500);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Upload Documents</h1>
        <p className="text-sm text-slate-500">Ingest PDFs, DOCX, or TXT files for processing.</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-slate-300 rounded-xl p-12 flex flex-col items-center justify-center bg-slate-50 hover:bg-blue-50 hover:border-blue-300 transition-all hover:scale-[1.02] duration-200 cursor-pointer relative"
          >
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.txt"
              onChange={handleFileInput}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-4">
              <UploadCloud className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-1">Drag & Drop files here</h3>
            <p className="text-sm text-slate-500 mb-4">or click to browse from your computer</p>
            <span className="text-xs text-slate-400">Supported: PDF, DOCX, TXT (max 50MB)</span>
          </div>

          {files.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 bg-slate-50 font-medium text-slate-700">
                Selected Files ({files.length})
              </div>
              <ul className="divide-y divide-slate-100">
                {files.map((entry, i) => (
                  <li key={i} className="px-4 py-3 flex items-center justify-between hover:bg-slate-50">
                    <div className="flex items-center gap-3">
                      {entry.status === "done" ? (
                        <CheckCircle className="w-5 h-5 text-emerald-500" />
                      ) : entry.status === "uploading" ? (
                        <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                      ) : entry.status === "error" ? (
                        <AlertCircle className="w-5 h-5 text-rose-500" />
                      ) : (
                        <FileText className="w-5 h-5 text-blue-500" />
                      )}
                      <div>
                        <p className="text-sm font-medium text-slate-900">{entry.name}</p>
                        <p className="text-xs text-slate-500">
                          {entry.status === "error" ? entry.error : entry.size}
                        </p>
                      </div>
                    </div>
                    {entry.status === "pending" && (
                      <button onClick={() => removeFile(i)} className="text-slate-400 hover:text-rose-500 p-1">
                        <X className="w-4 h-4" />
                      </button>
                    )}
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
              <select value={docType} onChange={e => setDocType(e.target.value)} className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                <option>Regulation (FAR/DFARS)</option>
                <option>RFP / Solicitation</option>
                <option>Internal Policy</option>
                <option>Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Tags (Comma separated)</label>
              <input value={tags} onChange={e => setTags(e.target.value)} type="text" placeholder="e.g., cyber, compliance, 2026" className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
            <div className="pt-4 border-t border-slate-100">
              <button
                onClick={handleStartProcessing}
                disabled={files.length === 0 || uploading}
                className="w-full bg-blue-600 text-white rounded-lg py-2.5 font-medium flex items-center justify-center gap-2 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {uploading ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Uploading...</>
                ) : (
                  <><Play className="w-4 h-4" /> Start Processing</>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
