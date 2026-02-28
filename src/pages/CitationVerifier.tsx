import { useState, useEffect } from "react";
import { CheckCircle, AlertTriangle, RefreshCw, Edit2, Loader2 } from "lucide-react";
import { apiFetch } from "../lib/api";

type Claim = {
  claim: string;
  original: string;
  ref: number;
  match_score: number;
  source_snippet: string;
  status: "verified" | "hallucination";
};

export default function CitationVerifier() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [queryText, setQueryText] = useState("");
  const [issueCount, setIssueCount] = useState(0);

  useEffect(() => {
    fetchLatestVerification();
  }, []);

  const fetchLatestVerification = async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/query/history?limit=1");
      if (!res.ok) { setLoading(false); return; }
      const history = await res.json();
      if (history.length === 0) { setLoading(false); return; }

      const latest = history[0];
      setQueryText(latest.query_text);

      // Extract verification data from agent_logs
      const verifyStep = (latest.agent_logs || []).find((s: any) => s.step === "verify");
      if (!verifyStep) { setLoading(false); return; }

      // Re-fetch full query details to get full verification data
      const detailRes = await apiFetch(`/api/v1/query/${latest.id}`);
      if (!detailRes.ok) { setLoading(false); return; }
      const detail = await detailRes.json();

      const allClaims: Claim[] = [];
      const logs = detail.agent_logs || [];
      const vStep = logs.find((s: any) => s.step === "verify");

      if (vStep && vStep.output) {
        // Build claims from the verify step output info
        const verified = vStep.output.verified_count || 0;
        const hallucinations = vStep.output.hallucination_count || 0;
        setIssueCount(hallucinations);

        // Parse log messages to reconstruct claims
        for (const log of vStep.logs || []) {
          if (log.startsWith("✓ Claim verified")) {
            const scoreMatch = log.match(/score: (\d+)%/);
            const refMatch = log.match(/\[(\d+)\]/);
            allClaims.push({
              claim: log.replace(/^✓ Claim verified against \[\d+\] \(score: \d+%\)/, "").trim() || "Verified claim",
              original: log,
              ref: refMatch ? parseInt(refMatch[1]) : 0,
              match_score: scoreMatch ? parseInt(scoreMatch[1]) / 100 : 0.9,
              source_snippet: "Source text matched successfully",
              status: "verified",
            });
          } else if (log.startsWith("✗ HALLUCINATION")) {
            const scoreMatch = log.match(/score: (\d+)%/);
            const textMatch = log.match(/"([^"]+)"/);
            allClaims.push({
              claim: textMatch ? textMatch[1] : "Unverified claim",
              original: log,
              ref: 0,
              match_score: scoreMatch ? parseInt(scoreMatch[1]) / 100 : 0,
              source_snippet: "No matching text found in retrieved context.",
              status: "hallucination",
            });
          }
        }
      }

      setClaims(allClaims);
    } catch (e) {
      console.error("Failed to fetch verification data", e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Citation Verification Panel</h1>
          <p className="text-sm text-slate-500">Real verification results from the latest query's Red Team agent.</p>
          {queryText && <p className="text-xs text-blue-600 mt-1">Latest query: "{queryText}"</p>}
        </div>
        <div className="flex gap-3">
          <button onClick={fetchLatestVerification} className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-slate-50 flex items-center gap-2 transition-colors">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>
      </div>

      {claims.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-12 text-center text-slate-500">
          No verification data yet. Run a query in Query Chat first.
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
            <h2 className="font-semibold text-slate-800">Claims Analysis</h2>
            <span className={`px-3 py-1 text-xs font-bold rounded-full uppercase tracking-wider ${issueCount > 0 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>
              {issueCount > 0 ? `${issueCount} Issue${issueCount > 1 ? 's' : ''} Detected` : 'All Verified'}
            </span>
          </div>
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500 bg-white">
              <tr>
                <th className="px-6 py-4 font-medium w-1/3">Claim</th>
                <th className="px-6 py-4 font-medium">Source Ref</th>
                <th className="px-6 py-4 font-medium">Score</th>
                <th className="px-6 py-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {claims.map((claim, i) => (
                <tr key={i} className={`hover:bg-slate-50 transition-colors ${claim.status === 'hallucination' ? 'bg-rose-50/30' : ''}`}>
                  <td className="px-6 py-4 text-slate-800 leading-relaxed">{claim.claim}</td>
                  <td className="px-6 py-4">
                    <span className="text-xs font-bold text-blue-600">[{claim.ref}]</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`font-mono text-xs font-bold ${claim.match_score > 0.6 ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {(claim.match_score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {claim.status === 'verified' ? (
                        <><CheckCircle className="w-4 h-4 text-emerald-500" /><span className="text-emerald-700 font-medium">Verified</span></>
                      ) : (
                        <><AlertTriangle className="w-4 h-4 text-rose-500" /><span className="text-rose-700 font-medium">Unverified</span></>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
