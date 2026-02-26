import { useState } from "react";
import { Send, Paperclip, Bookmark, Save, ShieldCheck } from "lucide-react";

export default function QueryChat() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hello! I'm your FAR compliance assistant. How can I help you today?", citations: [] }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const newMessages = [...messages, { role: "user", content: input, citations: [] }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();
      setMessages([...newMessages, { role: "assistant", content: data.response, citations: ["FAR 15.403-1"] }]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-50 border border-slate-200 rounded-xl shadow-sm overflow-hidden font-sans">
      <div className="p-4 border-b border-slate-200 bg-white flex justify-between items-center">
        <div>
          <h2 className="font-bold text-slate-800 tracking-tight">Query Chat</h2>
          <p className="text-xs text-slate-500">Ask natural questions; receive citation-backed answers.</p>
        </div>
        <div className="flex gap-2">
          <span className="px-2 py-1 bg-blue-50 text-blue-600 text-xs font-bold rounded-md uppercase tracking-wider">FAR Scope</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl p-5 shadow-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-sm' : 'bg-white border border-slate-200 text-slate-800 rounded-bl-sm'}`}>
              <p className="whitespace-pre-wrap leading-relaxed text-[15px]">{msg.content}</p>
              
              {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-100">
                  <div className="flex items-center gap-2 mb-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-500" />
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Verified Citations</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {msg.citations.map((cit, idx) => (
                      <span key={idx} className="px-2 py-1 bg-slate-100 text-slate-600 text-xs font-medium rounded-md hover:bg-slate-200 cursor-pointer transition-colors">
                        {cit}
                      </span>
                    ))}
                  </div>
                  <div className="flex justify-end gap-3 mt-3">
                    <button className="text-slate-400 hover:text-blue-600 transition-colors" title="Save Response"><Save className="w-4 h-4" /></button>
                    <button className="text-slate-400 hover:text-blue-600 transition-colors" title="Bookmark"><Bookmark className="w-4 h-4" /></button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-bl-sm p-5 shadow-sm flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 bg-white border-t border-slate-200">
        <div className="flex gap-2 mb-3 overflow-x-auto pb-2 scrollbar-hide">
          {["What is the micro-purchase threshold?", "Explain FAR Part 15", "Set-aside rules for IT services"].map((chip, i) => (
            <button key={i} onClick={() => setInput(chip)} className="whitespace-nowrap px-3 py-1.5 bg-slate-100 text-slate-600 text-xs font-medium rounded-full hover:bg-slate-200 transition-colors">
              {chip}
            </button>
          ))}
        </div>
        <form onSubmit={handleSend} className="flex gap-2 items-end">
          <button type="button" className="p-3 text-slate-400 hover:text-slate-600 bg-slate-50 rounded-xl border border-slate-200 transition-colors">
            <Paperclip className="w-5 h-5" />
          </button>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about regulations..."
            className="flex-1 border border-slate-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none bg-slate-50"
            rows={1}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend(e);
              }
            }}
          />
          <button type="submit" disabled={loading || !input.trim()} className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-sm shadow-blue-600/20">
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
