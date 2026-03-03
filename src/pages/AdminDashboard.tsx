import { useState, useEffect } from "react";
import { Activity, Server, AlertTriangle, DollarSign, RefreshCw, Loader2 } from "lucide-react";
import { apiFetch } from "../lib/api";

export default function AdminDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [llmConfig, setLlmConfig] = useState<any>(null);
  const [discovery, setDiscovery] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [updatingLlm, setUpdatingLlm] = useState(false);
  const [ticker, setTicker] = useState("");
  const [hfDataset, setHfDataset] = useState("");
  const [clQuery, setClQuery] = useState("");
  const [kaggleSlug, setKaggleSlug] = useState("");
  const [pubmedQuery, setPubmedQuery] = useState("");
  const [specPlatform, setSpecPlatform] = useState("");
  const [ingesting, setIngesting] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, logsRes, configRes, discoveryRes] = await Promise.all([
        apiFetch("/api/v1/admin/stats"),
        apiFetch("/api/v1/admin/audit-logs?limit=20"),
        apiFetch("/api/v1/admin/llm-config"),
        apiFetch("/api/v1/admin/discovery"),
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (logsRes.ok) setAuditLogs(await logsRes.json());
      if (configRes.ok) setLlmConfig(await configRes.json());
      if (discoveryRes.ok) setDiscovery(await discoveryRes.json());
    } finally {
      setLoading(false);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const res = await apiFetch("/api/v1/admin/seed-datasets", { method: "POST" });
      if (res.ok) {
        alert("Knowledge ingestion started in background.");
      }
    } finally {
      setSeeding(false);
    }
  };

  const handleSecIngest = async () => {
    if (!ticker) return;
    setIngesting(true);
    try {
      const res = await apiFetch("/api/v1/admin/ingest/sec", {
        method: "POST",
        body: JSON.stringify({ ticker }),
      });
      if (res.ok) alert(`Ingestion for ${ticker.toUpperCase()} started.`);
    } finally { setIngesting(false); setTicker(""); }
  };

  const handleHfIngest = async () => {
    if (!hfDataset) return;
    setIngesting(true);
    try {
      const res = await apiFetch("/api/v1/admin/ingest/hf", {
        method: "POST",
        body: JSON.stringify({ dataset_name: hfDataset, limit: 100 }),
      });
      if (res.ok) alert(`Ingestion for ${hfDataset} started.`);
    } finally { setIngesting(false); setHfDataset(""); }
  };

  const handleClIngest = async () => {
    if (!clQuery) return;
    setIngesting(true);
    try {
      const res = await apiFetch("/api/v1/admin/ingest/courtlistener", {
        method: "POST",
        body: JSON.stringify({ query: clQuery, limit: 3 }),
      });
      if (res.ok) alert(`CourtListener ingestion for "${clQuery}" started.`);
    } finally { setIngesting(false); setClQuery(""); }
  };

  const handleKaggleIngest = async () => {
    if (!kaggleSlug) return;
    setIngesting(true);
    try {
      const res = await apiFetch("/api/v1/admin/ingest/kaggle", {
        method: "POST",
        body: JSON.stringify({ dataset_slug: kaggleSlug }),
      });
      if (res.ok) alert(`Kaggle ingestion for ${kaggleSlug} started.`);
    } finally { setIngesting(false); setKaggleSlug(""); }
  };

  const handlePubmedIngest = async () => {
    if (!pubmedQuery) return;
    setIngesting(true);
    try {
      const res = await apiFetch("/api/v1/admin/ingest/pubmed", {
        method: "POST",
        body: JSON.stringify({ query: pubmedQuery }),
      });
      if (res.ok) alert(`PubMed ingestion for "${pubmedQuery}" started.`);
    } finally { setIngesting(false); setPubmedQuery(""); }
  };

  const handleSpecIngest = async (p: string) => {
    setIngesting(true);
    try {
      const res = await apiFetch("/api/v1/admin/ingest/specialized", {
        method: "POST",
        body: JSON.stringify({ platform: p }),
      });
      if (res.ok) alert(`Specialized ingestion for ${p} started.`);
    } finally { setIngesting(false); }
  };

  const handleRegIngest = async (region: string) => {
    setIngesting(true);
    try {
      const res = await apiFetch("/api/v1/admin/ingest/regulations", {
        method: "POST",
        body: JSON.stringify({ region }),
      });
      if (res.ok) alert(`Regulatory ingestion for ${region} started.`);
    } finally { setIngesting(false); }
  };

  const handleUpdateLlm = async (provider: string) => {
    setUpdatingLlm(true);
    try {
      const res = await apiFetch("/api/v1/admin/llm-config", {
        method: "PUT",
        body: JSON.stringify({ provider }),
      });
      if (res.ok) {
        setLlmConfig((prev: any) => ({ ...prev, current_provider: provider }));
      }
    } finally {
      setUpdatingLlm(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const statCards = stats ? [
    { label: "Total Users", value: stats.total_users, icon: Server, color: "text-blue-600", bg: "bg-blue-100" },
    { label: "Queries Today", value: stats.queries_today, icon: Activity, color: "text-emerald-600", bg: "bg-emerald-100" },
    { label: "Total Queries", value: stats.total_queries, icon: Activity, color: "text-indigo-600", bg: "bg-indigo-100" },
    { label: "Est. Token Cost", value: `$${stats.estimated_cost}`, icon: DollarSign, color: "text-amber-600", bg: "bg-amber-100" },
  ] : [];

  return (
    <div className="max-w-6xl mx-auto space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">System Dashboard</h1>
          <p className="text-sm text-slate-500">Live platform health and audit logs from the backend.</p>
        </div>
        <button onClick={fetchData} className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-slate-50 flex items-center gap-2 transition-colors">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div key={i} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${stat.bg} ${stat.color}`}>
                <Icon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">{stat.label}</p>
                <p className="text-2xl font-bold text-slate-900">{stat.value}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 overflow-hidden">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Knowledge Explorer</h2>
            <p className="text-xs text-slate-500">Premium LLM training & RAG datasets identified for enterprise compliance.</p>
          </div>
          <div className="flex gap-2">
            {discovery && Object.entries(discovery.platforms).map(([p, link]: [string, any]) => (
              <a key={p} href={link} target="_blank" rel="noopener" className="text-[10px] font-bold px-2 py-1 bg-slate-100 text-slate-600 rounded hover:bg-slate-200 transition-colors">
                {p}
              </a>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {discovery && discovery.datasets.map((ds: any) => (
            <div key={ds.id} className="p-4 rounded-lg border border-slate-100 bg-slate-50/50 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] uppercase font-bold text-blue-600 px-1.5 py-0.5 bg-blue-50 rounded">
                    {ds.category}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 truncate">{ds.id.replace(/_/g, ' ')}</h3>
                <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">{ds.description}</p>
              </div>
              <div className="mt-4 flex gap-2">
                {ds.huggingface && (
                  <a href={`https://huggingface.co/datasets/${ds.huggingface}`} target="_blank" className="text-[10px] font-bold text-blue-500 hover:underline">Hugging Face</a>
                )}
                {ds.api && (
                  <a href={ds.api} target="_blank" className="text-[10px] font-bold text-emerald-500 hover:underline">API Docs</a>
                )}
                {['fineweb', 'cosmopedia', 'the_stack', 'common_corpus'].includes(ds.id.toLowerCase()) && (
                  <button
                    onClick={() => handleSpecIngest(ds.id.toLowerCase())}
                    disabled={ingesting}
                    className="text-[10px] font-bold text-slate-700 bg-white border border-slate-200 px-1.5 py-0.5 rounded hover:bg-slate-50 disabled:opacity-50"
                  >
                    Auto-Pull
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 text-slate-900">System Metrics</h2>
          {stats && (
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 border border-slate-100 rounded-lg bg-slate-50">
                <p className="text-sm text-slate-500 mb-1">Total Documents</p>
                <p className="text-xl font-bold text-slate-900">{stats.total_documents}</p>
              </div>
              <div className="p-4 border border-slate-100 rounded-lg bg-slate-50">
                <p className="text-sm text-slate-500 mb-1">Vector Chunks</p>
                <p className="text-xl font-bold text-slate-900">{stats.vector_chunks}</p>
              </div>
              <div className="p-4 border border-slate-100 rounded-lg bg-slate-50">
                <p className="text-sm text-slate-500 mb-1">Avg Confidence</p>
                <p className="text-xl font-bold text-slate-900">{(stats.avg_confidence * 100).toFixed(1)}%</p>
              </div>
              <div className="p-4 border border-slate-100 rounded-lg bg-slate-50">
                <p className="text-sm text-slate-500 mb-1">Avg Response Time</p>
                <p className="text-xl font-bold text-slate-900">{stats.avg_response_time_ms}ms</p>
              </div>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 text-slate-900 flex items-center gap-2">
            <Server className="w-5 h-5 text-blue-500" />
            LLM Providers (Free Tier Ready)
          </h2>
          <div className="space-y-3">
            {llmConfig && Object.entries(llmConfig.providers).map(([name, info]: [string, any]) => (
              <button
                key={name}
                onClick={() => handleUpdateLlm(name)}
                disabled={!info.has_key || updatingLlm}
                className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all ${llmConfig.current_provider === name
                  ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500'
                  : 'border-slate-100 bg-slate-50 hover:border-slate-300'
                  } ${!info.has_key ? 'opacity-50 grayscale cursor-not-allowed' : ''}`}
              >
                <div className="flex flex-col items-start">
                  <span className="text-sm font-bold capitalize">{name}</span>
                  <span className="text-[10px] text-slate-500">{info.has_key ? 'Key Configured' : 'No Key Found'}</span>
                </div>
                {llmConfig.current_provider === name && (
                  <div className="w-2 h-2 rounded-full bg-blue-500 shadow-sm shadow-blue-500/50" />
                )}
              </button>
            ))}
          </div>
          <div className="mt-6 pt-6 border-t border-slate-100 space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Knowledge Base Live Hub</h3>
            <p className="text-xs text-slate-500">Pull latext filings and datasets directly into the vector engine.</p>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Ticker (e.g. AAPL)"
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                className="flex-1 text-xs border border-slate-200 rounded px-3 py-2 outline-none focus:border-blue-400"
              />
              <button
                onClick={handleSecIngest}
                disabled={ingesting || !ticker}
                className="bg-blue-600 text-white text-[10px] font-bold px-3 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Pull SEC
              </button>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="HF: user/dataset"
                value={hfDataset}
                onChange={(e) => setHfDataset(e.target.value)}
                className="flex-1 text-xs border border-slate-200 rounded px-3 py-2 outline-none focus:border-blue-400"
              />
              <button
                onClick={handleHfIngest}
                disabled={ingesting || !hfDataset}
                className="bg-emerald-600 text-white text-[10px] font-bold px-3 py-2 rounded hover:bg-emerald-700 disabled:opacity-50"
              >
                Pull HF
              </button>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Law Query (e.g. copyright)"
                value={clQuery}
                onChange={(e) => setClQuery(e.target.value)}
                className="flex-1 text-xs border border-slate-200 rounded px-3 py-2 outline-none focus:border-blue-400"
              />
              <button
                onClick={handleClIngest}
                disabled={ingesting || !clQuery}
                className="bg-indigo-600 text-white text-[10px] font-bold px-3 py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
              >
                Pull Law
              </button>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Kaggle Slug (user/dataset)"
                value={kaggleSlug}
                onChange={(e) => setKaggleSlug(e.target.value)}
                className="flex-1 text-xs border border-slate-200 rounded px-3 py-2 outline-none focus:border-blue-400"
              />
              <button
                onClick={handleKaggleIngest}
                disabled={ingesting || !kaggleSlug}
                className="bg-amber-600 text-white text-[10px] font-bold px-3 py-2 rounded hover:bg-amber-700 disabled:opacity-50"
              >
                Pull Kaggle
              </button>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="PubMed Search"
                value={pubmedQuery}
                onChange={(e) => setPubmedQuery(e.target.value)}
                className="flex-1 text-xs border border-slate-200 rounded px-3 py-2 outline-none focus:border-blue-400"
              />
              <button
                onClick={handlePubmedIngest}
                disabled={ingesting || !pubmedQuery}
                className="bg-rose-600 text-white text-[10px] font-bold px-3 py-2 rounded hover:bg-rose-700 disabled:opacity-50"
              >
                Pull Sci
              </button>
            </div>

            <div className="pt-4 border-t border-slate-100 flex flex-col gap-2">
              <h3 className="text-xs font-bold text-slate-800">Global Regulatory Seeds</h3>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleRegIngest("EU")}
                  disabled={ingesting}
                  className="bg-slate-800 text-white text-[10px] font-bold py-2 rounded hover:bg-black disabled:opacity-50"
                >
                  Pull EU (GDPR/AI Act)
                </button>
                <button
                  onClick={() => handleRegIngest("US")}
                  disabled={ingesting}
                  className="bg-slate-800 text-white text-[10px] font-bold py-2 rounded hover:bg-black disabled:opacity-50"
                >
                  Pull US (CCPA/HIPAA)
                </button>
              </div>
            </div>

            <button
              onClick={handleSeed}
              disabled={seeding}
              className="w-full py-2 bg-slate-900 text-white rounded-lg text-sm font-bold hover:bg-black transition-colors flex items-center justify-center gap-2"
            >
              {seeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Seed Static Datasets
            </button>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 text-slate-900">Recent Audit Logs</h2>
          <div className="space-y-4 max-h-80 overflow-y-auto">
            {auditLogs.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No audit logs yet.</p>
            ) : (
              auditLogs.map((log) => (
                <div key={log.id} className="flex gap-3">
                  <div className="mt-1">
                    <div className={`w-2 h-2 rounded-full ${log.action.includes('FAIL') || log.action.includes('ERROR') ? 'bg-rose-500' :
                      log.action.includes('LOGIN') || log.action.includes('REGISTER') ? 'bg-blue-500' :
                        'bg-slate-400'
                      }`} />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">{log.action}</p>
                    <p className="text-xs text-slate-500 truncate max-w-[200px]">{log.detail || log.resource || "—"}</p>
                    <p className="text-xs text-slate-400 mt-1">{new Date(log.timestamp).toLocaleString()}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
