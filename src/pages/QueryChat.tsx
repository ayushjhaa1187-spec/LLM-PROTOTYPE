import React, { useState, useEffect } from "react";
import { Send, FileText, ShieldCheck, Loader2, Activity, Globe } from "lucide-react";
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
  contract_analysis?: any;
  compliance_analysis?: any;
  is_blocked?: boolean;
  blocking_reason?: string;
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
        content: data.is_blocked ? "⚠️ This response was blocked due to an accuracy or policy violation." : data.answer,
        citations: data.citations || [],
        confidence: data.confidence,
        queryId: data.id,
        is_blocked: data.is_blocked,
        blocking_reason: data.blocking_reason
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
    <div className="h-full flex flex-col bg-[#F8FAFC] border border-slate-200 rounded-2xl shadow-2xl overflow-hidden font-sans backdrop-blur-sm">
      <div className="p-5 border-b border-slate-200/60 bg-white/80 backdrop-blur-md flex justify-between items-center z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="font-extrabold text-slate-900 tracking-tight text-lg">FAR Compliance Copilot</h2>
            <p className="text-[11px] text-slate-500 font-medium uppercase tracking-wider">Enterprise RAG Engine • Secure Audit</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end">
            <span className="text-[10px] font-bold text-emerald-600 uppercase">System Status</span>
            <span className="text-xs text-slate-400 flex items-center gap-1.5 font-medium"><div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" /> Local-Vector Ready</span>
          </div>
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50 scroll-smooth">
        {messages.map((msg, i) => (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ type: "spring", duration: 0.5, bounce: 0.3 }}
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} group`}
          >
            <div className={`max-w-[85%] rounded-[2.5rem] p-6 transition-all duration-300 ${msg.role === 'user'
                ? 'bg-gradient-to-br from-blue-600 to-indigo-700 text-white rounded-br-none shadow-xl shadow-blue-500/20'
                : 'bg-white/70 backdrop-blur-xl border border-white/40 text-slate-800 rounded-bl-none shadow-lg'
              }`}>
              <p className="whitespace-pre-wrap leading-relaxed text-[15.5px] font-medium tracking-tight">{msg.content}</p>

              {msg.contract_analysis && (
                <div className="mt-5 p-5 rounded-[1.8rem] bg-indigo-50/50 backdrop-blur-md border border-indigo-100/50 space-y-4 shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-200/20 rounded-full -mr-16 -mt-16 blur-3xl" />
                  <div className="flex items-center gap-2 text-indigo-700 font-bold text-[11px] uppercase tracking-[0.2em] relative z-10">
                    <Activity className="w-4 h-4" /> AI Auditor: Contract Analysis
                  </div>
                  <p className="text-[15px] text-slate-800 font-bold relative z-10 leading-snug">{msg.contract_analysis.summary}</p>

                  {msg.contract_analysis.risks?.length > 0 && (
                    <div className="space-y-3 pt-2 relative z-10">
                      {msg.contract_analysis.risks.map((r: any, idx: number) => (
                        <div key={idx} className="flex flex-col gap-2 text-xs bg-white/80 p-4 rounded-2xl border border-indigo-100 shadow-sm hover:shadow-md transition-shadow">
                          <div className="flex justify-between items-center">
                            <span className={`font-black px-2 py-1 rounded-lg text-[9px] uppercase tracking-tighter ${r.level === 'high' ? 'bg-rose-500 text-white' : 'bg-amber-400 text-slate-900'}`}>
                              {r.level} Risk Detection
                            </span>
                          </div>
                          <p className="font-bold text-slate-900 italic text-sm">"{r.clause}"</p>
                          <p className="text-slate-600 leading-normal">{r.reason}</p>
                          {r.remediation && (
                            <div className="mt-2 p-3 bg-blue-50 rounded-xl border-l-4 border-blue-500">
                              <p className="text-[10px] font-black text-blue-700 uppercase mb-1 tracking-widest">Remediation Strategy</p>
                              <p className="text-blue-900 font-medium leading-tight">{r.remediation}</p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="flex gap-8 pt-4 border-t border-indigo-100 relative z-10">
                    <div className="flex flex-col">
                      <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Active Obligations</span>
                      <span className="text-lg font-black text-slate-900">{msg.contract_analysis.obligations?.length || 0}</span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Compliance Gaps</span>
                      <span className="text-lg font-black text-rose-600">{msg.contract_analysis.compliance_issues?.length || 0}</span>
                    </div>
                  </div>
                </div>
              )}

              {msg.compliance_analysis && (
                <div className="mt-5 p-5 rounded-[1.8rem] bg-emerald-50/50 backdrop-blur-md border border-emerald-100/50 space-y-4 shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-200/20 rounded-full -mr-16 -mt-16 blur-3xl" />
                  <div className="flex items-center justify-between relative z-10">
                    <div className="flex items-center gap-2 text-emerald-800 font-bold text-[11px] uppercase tracking-[0.2em]">
                      <ShieldCheck className="w-4 h-4" /> Compliance Radar
                    </div>
                    <div className="bg-emerald-500 text-white px-3 py-1 rounded-full text-[13px] font-black shadow-lg shadow-emerald-500/30">
                      {msg.compliance_analysis.compliance_score}%
                    </div>
                  </div>

                  {msg.compliance_analysis.scoring_rationale && (
                    <p className="text-[11px] text-slate-600 font-medium bg-white/60 p-3 rounded-xl border border-emerald-50 relative z-10 leading-snug">
                      {msg.compliance_analysis.scoring_rationale}
                    </p>
                  )}

                  <div className="flex flex-wrap gap-2 relative z-10">
                    {msg.compliance_analysis.regions?.map((reg: string, idx: number) => (
                      <span key={idx} className="px-3 py-1 bg-white border border-emerald-100 text-emerald-700 rounded-lg text-[10px] font-black uppercase tracking-tighter">
                        {reg} Mapping
                      </span>
                    ))}
                  </div>

                  {msg.compliance_analysis.regulations?.length > 0 && (
                    <div className="space-y-2 relative z-10">
                      {msg.compliance_analysis.regulations.map((r: any, idx: number) => (
                        <div key={idx} className="flex flex-col text-xs bg-white/80 p-3 rounded-xl border border-emerald-50 shadow-sm transition-transform hover:translate-x-1">
                          <span className="font-extrabold text-slate-900">{r.name}</span>
                          <span className="text-slate-500 text-[11px] mt-0.5">{r.impact}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {msg.compliance_analysis.recommended_actions?.length > 0 && (
                    <div className="pt-3 border-t border-emerald-100 relative z-10">
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Conformity Checklist</p>
                      <div className="grid grid-cols-1 gap-2">
                        {msg.compliance_analysis.recommended_actions.map((act: string, idx: number) => (
                          <div key={idx} className="flex items-start gap-2 bg-white/30 p-2 rounded-lg">
                            <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full mt-1 shrink-0" />
                            <span className="text-[11.5px] text-slate-700 font-medium leading-tight">{act}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {msg.is_blocked && (
                <div className="mt-4 p-4 rounded-xl bg-red-50 border border-red-200 shadow-inner">
                  <div className="flex items-center gap-2 text-red-700 font-bold text-xs uppercase tracking-wider mb-2">
                    <ShieldCheck className="w-4 h-4" /> AI Hallucination Guard Triggered
                  </div>
                  <p className="text-sm text-red-900 leading-relaxed font-medium">
                    {msg.blocking_reason || "This response was flagged as medically, legally, or factually inaccurate compared to our vector dataset."}
                  </p>
                  <p className="mt-2 text-[10px] text-red-600 uppercase font-bold tracking-widest">Event triggered: compliance.failed webhook sent to admin.</p>
                </div>
              )}

              {msg.role === 'assistant' && msg.confidence !== undefined && !msg.is_blocked && (
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
