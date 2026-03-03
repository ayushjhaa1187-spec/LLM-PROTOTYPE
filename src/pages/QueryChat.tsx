import React, { useState, useEffect } from "react";
import { Send, FileText, Bookmark, Save, ShieldCheck, AlertTriangle, Loader2, Activity, Globe } from "lucide-react";
import { motion } from "motion/react";
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
  const [globalLoading, setGlobalLoading] = useState(false);
  const [globalResults, setGlobalResults] = useState<any>(null);
  const [globalDiscoveryActive, setGlobalDiscoveryActive] = useState(false);
  const [docs, setDocs] = useState<any[]>([]);
  const [selectedDocId, setSelectedDocId] = useState("");
  const scrollRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

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

  const handleDownloadReport = async (msg: any) => {
    try {
      const res = await apiFetch("/api/v1/query/export-pdf", {
        method: "POST",
        body: JSON.stringify({
          query: messages.find(m => m.role === 'user')?.content || "Compliance Inquiry",
          answer: msg.content,
          contract_analysis: msg.contract_analysis,
          compliance_analysis: msg.compliance_analysis,
        }),
      });

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "compliance_report.pdf";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed", err);
    }
  };

  const handleGlobalSearch = async () => {
    if (!input) return;
    setGlobalLoading(true);
    setGlobalDiscoveryActive(true);
    setMessages(prev => [...prev, { role: "user", content: `Global Discovery: ${input}`, citations: [] }]);

    try {
      const res = await apiFetch("/api/v1/query/global-search", {
        method: "POST",
        body: JSON.stringify({ query: input }),
      });
      const data = await res.json();
      setGlobalResults(data);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: `Global discovery complete. I've searched Local, CourtListener, and SEC Edgar. \n\nFound in CourtListener: ${data.courtlistener.join(', ') || 'None'}\nFound in SEC: ${data.sec.join(', ') || 'None'}`,
        citations: [],
      }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: `Error during global search: ${err instanceof Error ? err.message : String(err)}`,
        citations: [],
      }]);
    } finally {
      setGlobalLoading(false);
      setInput("");
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading || globalLoading) return;

    const userMsg: Message = { role: "user", content: input, citations: [] };
    setMessages(prev => [...prev, userMsg]);
    const query = input;
    setInput("");
    setLoading(true);
    setGlobalDiscoveryActive(false); // Reset global discovery active state

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

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50 scroll-smooth">
        {messages.map((msg, i) => (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[80%] rounded-2xl p-5 shadow-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-sm' : 'bg-white border border-slate-200 text-slate-800 rounded-bl-sm'}`}>
              <p className="whitespace-pre-wrap leading-relaxed text-[15px]">{msg.content}</p>

              {msg.contract_analysis && (
                <div className="mt-4 p-4 rounded-xl bg-indigo-50 border border-indigo-100 space-y-3 shadow-inner">
                  <div className="flex items-center gap-2 text-indigo-700 font-bold text-[10px] uppercase tracking-widest">
                    <Activity className="w-3.5 h-3.5" /> Special Insight: Contract Analysis
                  </div>
                  <p className="text-sm text-slate-700 font-semibold">{msg.contract_analysis.summary}</p>

                  {msg.contract_analysis.risks?.length > 0 && (
                    <div className="space-y-1.5 pt-2">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Critical Risks</p>
                      {msg.contract_analysis.risks.map((r: any, idx: number) => (
                        <div key={idx} className="flex flex-col gap-1 text-xs bg-white/60 p-3 rounded border border-indigo-50 shadow-sm">
                          <div className="flex justify-between items-start mb-1">
                            <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] uppercase ${r.level === 'high' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'}`}>
                              {r.level} Risk
                            </span>
                          </div>
                          <p className="font-medium text-slate-800 italic">"{r.clause}"</p>
                          <p className="text-slate-500 mt-1">{r.reason}</p>
                          {r.remediation && (
                            <div className="mt-2 p-2 bg-indigo-100/50 rounded border-l-2 border-indigo-500">
                              <p className="text-[10px] font-bold text-indigo-700 uppercase mb-0.5">Proposed Remediation</p>
                              <p className="text-indigo-900 leading-tight">{r.remediation}</p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="flex gap-6 pt-3 border-t border-indigo-100/50">
                    <div className="flex flex-col">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Obligations</span>
                      <span className="text-sm font-bold text-indigo-600">{msg.contract_analysis.obligations?.length || 0}</span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Compliance Issues</span>
                      <span className="text-sm font-bold text-rose-500">{msg.contract_analysis.compliance_issues?.length || 0}</span>
                    </div>
                  </div>
                </div>
              )}

              {msg.compliance_analysis && (
                <div className="mt-4 p-4 rounded-xl bg-emerald-50 border border-emerald-100 space-y-3 shadow-inner">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-emerald-700 font-bold text-[10px] uppercase tracking-widest">
                      <ShieldCheck className="w-3.5 h-3.5" /> Compliance Radar
                    </div>
                    <span className="text-xs font-bold text-emerald-600">Score: {msg.compliance_analysis.compliance_score}%</span>
                  </div>

                  {msg.compliance_analysis.scoring_rationale && (
                    <p className="text-[10px] text-slate-500 italic bg-white/40 p-1.5 rounded border border-emerald-50">
                      Rationale: {msg.compliance_analysis.scoring_rationale}
                    </p>
                  )}

                  <div className="flex flex-wrap gap-1.5">
                    {msg.compliance_analysis.regions?.map((reg: string, idx: number) => (
                      <span key={idx} className="px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full text-[10px] font-bold border border-emerald-200 uppercase">
                        {reg}
                      </span>
                    ))}
                  </div>

                  {msg.compliance_analysis.regulations?.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Applicable Regulations</p>
                      {msg.compliance_analysis.regulations.map((r: any, idx: number) => (
                        <div key={idx} className="flex flex-col text-xs bg-white/60 p-2 rounded border border-emerald-50">
                          <span className="font-bold text-slate-800">{r.name} ({r.region})</span>
                          <span className="text-slate-500 text-[11px]">{r.impact}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {msg.compliance_analysis.recommended_actions?.length > 0 && (
                    <div className="pt-2 border-t border-emerald-100/50">
                      <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Recommended Actions</p>
                      <ul className="list-disc list-inside space-y-0.5">
                        {msg.compliance_analysis.recommended_actions.map((act: string, idx: number) => (
                          <li key={idx} className="text-[11px] text-slate-600 leading-tight">{act}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {msg.role === 'assistant' && msg.confidence !== undefined && (
                <div className="mt-3 flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${msg.confidence >= 0.7 ? 'bg-emerald-500' : msg.confidence >= 0.4 ? 'bg-amber-500' : 'bg-rose-500'}`} />
                  <span className="text-xs font-medium text-slate-500">
                    Confidence: {(msg.confidence * 100).toFixed(0)}%
                  </span>
                  {(msg.contract_analysis || msg.compliance_analysis) && (
                    <button
                      onClick={() => handleDownloadReport(msg)}
                      className="ml-auto flex items-center gap-1.5 px-3 py-1 bg-slate-900 text-white text-[10px] font-bold rounded-lg hover:bg-black transition-colors"
                    >
                      <FileText className="w-3 h-3" /> Download Report
                    </button>
                  )}
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
          </motion.div>
        ))}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-bl-sm p-5 shadow-sm flex items-center gap-3">
              <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
              <span className="text-sm text-slate-500">Running RAG pipeline...</span>
            </div>
          </motion.div>
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
          <button
            type="button"
            onClick={handleGlobalSearch}
            disabled={globalLoading || loading || !input.trim()}
            className="p-3 mb-1 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm shadow-indigo-600/20"
            title="Global Deep Discovery (Search Remote Sources)"
          >
            {globalLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Globe className="w-5 h-5" />}
          </button>
          <button type="submit" disabled={loading || globalLoading || !input.trim()} className="p-3 mb-1 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-sm shadow-blue-600/20">
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </form>
      </div>
    </div>
  );
}
