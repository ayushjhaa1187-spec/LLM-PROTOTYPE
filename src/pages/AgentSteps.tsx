import { CheckCircle, Circle, Clock, Search, Edit3, ShieldCheck } from "lucide-react";

export default function AgentSteps() {
  const steps = [
    { id: 1, name: "Search Vector DB", status: "completed", time: "10:42:01", icon: Search, logs: ["Found 12 relevant chunks", "Top match: FAR 19.502-2 (Score: 0.92)"] },
    { id: 2, name: "Draft Response", status: "completed", time: "10:42:05", icon: Edit3, logs: ["Generating draft with citations", "Draft completed in 3.2s"] },
    { id: 3, name: "Verify Citations", status: "processing", time: "10:42:08", icon: ShieldCheck, logs: ["Checking claim 1 against FAR 19.502-2", "Checking claim 2 against FAR 19.502-3"] },
    { id: 4, name: "Finalize Output", status: "queued", time: "--:--:--", icon: CheckCircle, logs: [] },
  ];

  return (
    <div className="max-w-3xl mx-auto space-y-6 font-sans">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Agent Reasoning Steps</h1>
        <p className="text-sm text-slate-500">Live view of the RAG pipeline execution.</p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-8">
        <div className="space-y-8">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isLast = index === steps.length - 1;
            return (
              <div key={step.id} className="relative flex gap-6">
                {!isLast && (
                  <div className={\`absolute left-6 top-10 bottom-[-2rem] w-0.5 \${step.status === 'completed' ? 'bg-emerald-500' : 'bg-slate-200'}\`}></div>
                )}
                <div className="relative z-10 flex-shrink-0">
                  <div className={\`w-12 h-12 rounded-full flex items-center justify-center border-2 \${
                    step.status === 'completed' ? 'bg-emerald-100 border-emerald-500 text-emerald-600' :
                    step.status === 'processing' ? 'bg-blue-100 border-blue-500 text-blue-600 animate-pulse' :
                    'bg-slate-50 border-slate-300 text-slate-400'
                  }\`}>
                    <Icon className="w-5 h-5" />
                  </div>
                </div>
                <div className="flex-1 pt-2">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className={\`text-lg font-bold \${step.status === 'queued' ? 'text-slate-400' : 'text-slate-900'}\`}>{step.name}</h3>
                    <span className="text-xs font-mono text-slate-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {step.time}
                    </span>
                  </div>
                  <div className="space-y-2 mt-3">
                    {step.logs.map((log, i) => (
                      <div key={i} className="text-sm text-slate-600 bg-slate-50 border border-slate-100 p-2 rounded-md font-mono text-xs flex items-center gap-2">
                        <span className="text-blue-500">&gt;</span> {log}
                      </div>
                    ))}
                    {step.status === 'processing' && (
                      <div className="text-sm text-blue-600 font-mono text-xs flex items-center gap-2 animate-pulse">
                        <span className="text-blue-500">&gt;</span> Processing...
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
