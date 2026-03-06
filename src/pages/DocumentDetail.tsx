import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { FileText, Download, PlusCircle, Search, Loader2 } from "lucide-react";
import { apiFetch } from "../lib/api";

type Chunk = {
  id: string;
  page: number;
  section: string;
  text: string;
};

export default function DocumentDetail() {
  const { id } = useParams();
  const [doc, setDoc] = useState<any>(null);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const fetchDocAndChunks = async () => {
      setLoading(true);
      setError(null);
      try {
        const [docRes, chunksRes] = await Promise.all([
          apiFetch(`/api/v1/documents/${id}`),
          apiFetch(`/api/v1/documents/${id}/chunks`)
        ]);

        if (docRes.ok) {
          setDoc(await docRes.json());
        } else {
          setError("Failed to load document info");
        }
        if (chunksRes.ok) {
          setChunks(await chunksRes.json());
        }
      } catch (err) {
        console.error("Failed to load document info", err);
        setError("Network error while connecting to server");
      } finally {
        setLoading(false);
      }
    };
    fetchDocAndChunks();
  }, [id]);

  const filteredChunks = chunks.filter(c =>
    c.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.section.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="p-8 text-center text-slate-500">
        {error ? error : "Document not found"}
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto h-full flex flex-col space-y-4">
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-medium">Error:</span> {error}
          </div>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700">×</button>
        </div>
      )}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <FileText className="w-6 h-6 text-blue-600" /> {doc.filename}
          </h1>
          <p className="text-sm text-slate-500">Document ID: {doc.id} • Indexed Chunks: {doc.chunk_count}</p>
        </div>
        <div className="flex gap-3">
          <button className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-slate-50 flex items-center gap-2 transition-colors">
            <Download className="w-4 h-4" /> Raw Text
          </button>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-blue-700 flex items-center gap-2 transition-colors">
            <PlusCircle className="w-4 h-4" /> Add to Vector Index
          </button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-0">
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
            <h2 className="font-semibold text-slate-800">Source Viewer</h2>
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <button className="hover:text-slate-800">&lt;</button>
              <span>Page 1 of 45</span>
              <button className="hover:text-slate-800">&gt;</button>
            </div>
          </div>
          <div className="flex-1 p-6 overflow-y-auto bg-slate-100/50">
            <div className="bg-white shadow-sm border border-slate-200 p-8 min-h-[800px] font-serif text-slate-800 leading-relaxed">
              <h3 className="text-xl font-bold mb-4">{doc.filename} Preview</h3>
              <p className="mb-4 bg-yellow-100/50 p-1 rounded">
                Raw source viewer currently disabled. Viewing full embedded text chunks requires direct vector DB indexing navigation, see chunk list.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
            <h2 className="font-semibold text-slate-800">Extracted Chunks ({filteredChunks.length})</h2>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search chunks..."
                className="pl-9 pr-4 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {filteredChunks.length === 0 ? (
              <div className="p-8 text-center text-slate-500">No chunks available.</div>
            ) : filteredChunks.map((chunk) => (
              <div key={chunk.id} className="border border-slate-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-sm transition-all cursor-pointer group">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded uppercase tracking-wider">
                    {chunk.section}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">Page {chunk.page}</span>
                </div>
                <p className="text-sm text-slate-700 leading-relaxed font-mono text-xs">{chunk.text}</p>
                <div className="mt-3 text-xs text-slate-400 font-mono opacity-0 group-hover:opacity-100 transition-opacity">
                  ID: {chunk.id}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
