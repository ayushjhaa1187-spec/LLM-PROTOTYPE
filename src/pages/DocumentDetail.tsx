import { useParams } from "react-router-dom";
import { FileText, Download, PlusCircle, Search } from "lucide-react";

export default function DocumentDetail() {
  const { id } = useParams();

  const chunks = [
    { id: "c1", page: 1, section: "FAR 19.502-2", text: "(a) Before setting aside an acquisition under this paragraph, the contracting officer shall first consider whether there is a reasonable expectation that offers will be obtained from at least two responsible small business concerns (the \"Rule of Two\")." },
    { id: "c2", page: 1, section: "FAR 19.502-2", text: "(b) The contracting officer shall set aside any acquisition over the micro-purchase threshold for small business participation when there is a reasonable expectation that offers will be obtained from at least two responsible small business concerns." },
    { id: "c3", page: 2, section: "FAR 19.502-3", text: "Partial set-asides. (a) The contracting officer shall set aside a portion of an acquisition, except for construction, for exclusive small business participation when..." },
  ];

  return (
    <div className="h-full flex flex-col space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <FileText className="w-6 h-6 text-blue-600" /> FAR_Part_19_Small_Business.pdf
          </h1>
          <p className="text-sm text-slate-500">Document ID: {id || "1"} • Indexed in ChromaDB</p>
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
              <h3 className="text-xl font-bold mb-4">19.502-2 Total small business set-asides.</h3>
              <p className="mb-4 bg-yellow-100/50 p-1 rounded">
                (a) Before setting aside an acquisition under this paragraph, the contracting officer shall first consider whether there is a reasonable expectation that offers will be obtained from at least two responsible small business concerns (the "Rule of Two").
              </p>
              <p className="mb-4">
                (b) The contracting officer shall set aside any acquisition over the micro-purchase threshold for small business participation when there is a reasonable expectation that offers will be obtained from at least two responsible small business concerns.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
            <h2 className="font-semibold text-slate-800">Extracted Chunks ({chunks.length})</h2>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input type="text" placeholder="Search chunks..." className="pl-9 pr-4 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chunks.map((chunk) => (
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
