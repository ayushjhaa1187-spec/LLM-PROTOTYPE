import React, { useState, useEffect } from "react";
import { Send, FileText, Bookmark, Save, ShieldCheck, AlertTriangle, Loader2 } from "lucide-react";
import { apiFetch } from "../lib/api";

type Citation = {
  ref: number;
  source: string;
  page: number;
  text: string;
  confidence: number;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  confidence?: number;
  queryId?: string;
};

export default function QueryChat() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hello! I'm your FAR compliance assistant. Upload some regulation documents, then ask me questions — I'll answer with verified citations.", citations: [] }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [docs, setDocs] = useState<any[]>([]);
  const [selectedDocId, setSelectedDocId] = useState("");

  useEffect(() => {
    // Load available documents for scoping
    const loadDocs = async () => {
      try {
        const res = await apiFetch("/api/v1/documents");
        if (res.ok) {
          const data = await res.json();
          setDocs(data);
        }
      } catch (e) {
        console.error("Failed to load documents", e);
      }
    };
    loadDocs();
  }, []);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: "user", content: input, citations: [] };
    setMessages(prev => [...prev, userMsg]);
    const query = input;
    setInput("");
    setLoading(true);

    try {
      const payload: any = { query };
      if (selectedDocId) {
        payload.document_ids = [selectedDocId];
      }

      const res = await apiFetch("/api/v1/query", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessages(prev => [...prev, {
          role: "assistant",
          content: `Error: ${data.detail || "Something went wrong"}`,
          citations: [],
        }]);
        return;
      }

      const assistantMsg: Message = {
        role: "assistant",
        content: data.answer,
        citations: data.citations || [],
        confidence: data.confidence,
        queryId: data.id,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: `Network error: ${err.message}. Is the backend running?`,
        citations: [],
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-50 border border-slate-200 rounded-xl shadow-sm overflow-hidden font-sans">
      <div className="p-4 border-b border-slate-200 bg-white flex justify-between items-center">
        <div>
          <h2 className="font-bold text-slate-800 tracking-tight">Query Chat</h2>
          <p className="text-xs text-slate-500">Ask natural questions; receive citation-backed answers from your uploaded documents.</p>
        </div>
        <div className="flex gap-2">
          <span className="px-2 py-1 bg-blue-50 text-blue-600 text-xs font-bold rounded-md uppercase tracking-wider">RAG Pipeline</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl p-5 shadow-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-sm' : 'bg-white border border-slate-200 text-slate-800 rounded-bl-sm'}`}>
              <p className="whitespace-pre-wrap leading-relaxed text-[15px]">{msg.content}</p>

              {msg.role === 'assistant' && msg.confidence !== undefined && (
                <div className="mt-3 flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${msg.confidence >= 0.7 ? 'bg-emerald-500' : msg.confidence >= 0.4 ? 'bg-amber-500' : 'bg-rose-500'}`} />
                  <span className="text-xs font-medium text-slate-500">
                    Confidence: {(msg.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              )}

              {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-100">
                  <div className="flex items-center gap-2 mb-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-500" />
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Verified Citations ({msg.citations.length})</span>
                  </div>
                  <div className="space-y-2">
                    {msg.citations.map((cit, idx) => (
                      <div key={idx} className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold text-blue-600">[{cit.ref}] {cit.source} — Page {cit.page}</span>
                          <span className={`text-xs font-mono font-bold ${cit.confidence >= 0.7 ? 'text-emerald-600' : 'text-amber-600'}`}>
                            {(cit.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">{cit.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-bl-sm p-5 shadow-sm flex items-center gap-3">
              <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
              <span className="text-sm text-slate-500">Running RAG pipeline...</span>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 bg-white border-t border-slate-200">
        <div className="flex gap-2 mb-3 overflow-x-auto pb-2 scrollbar-hide">
          {["What is the micro-purchase threshold?", "Explain small business set-aside rules", "What are IT cybersecurity requirements?"].map((chip, i) => (
            <button key={i} onClick={() => setInput(chip)} className="whitespace-nowrap px-3 py-1.5 bg-slate-100 text-slate-600 text-xs font-medium rounded-full hover:bg-slate-200 transition-colors">
              {chip}
            </button>
          ))}
        </div>
        <form onSubmit={handleSend} className="flex gap-2 items-end">
          <div className="flex-1 border border-slate-300 rounded-xl bg-slate-50 flex flex-col overflow-hidden focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 transition-shadow">
            <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-200 bg-white">
              <FileText className="w-4 h-4 text-slate-400" />
              <select
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
                className="text-xs bg-transparent text-slate-600 outline-none flex-1 max-w-[200px]"
              >
                <option value="">All Documents</option>
                {docs.map(d => (
                  <option key={d.id} value={d.id}>{d.filename}</option>
                ))}
              </select>
            </div>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              className="px-4 py-3 outline-none resize-none bg-transparent w-full"
              rows={2}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(e);
                }
              }}
            />
          </div>
          <button type="submit" disabled={loading || !input.trim()} className="p-3 mb-1 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-sm shadow-blue-600/20">
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
