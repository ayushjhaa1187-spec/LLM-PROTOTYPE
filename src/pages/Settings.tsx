import { useState } from "react";
import { Save, Key, Database, Sliders, CheckCircle } from "lucide-react";

export default function Settings() {
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Settings & Configuration</h1>
          <p className="text-sm text-slate-500">Manage models, chunking, vector DBs, and API keys.</p>
        </div>
        <div className="flex items-center gap-3">
          {saved && <span className="text-sm font-medium text-emerald-600 flex items-center gap-1 min-w-[120px] transition-all"><CheckCircle className="w-4 h-4" /> Settings Saved</span>}
          <button onClick={handleSave} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-blue-700 flex items-center gap-2 transition-colors">
            <Save className="w-4 h-4" /> Save Changes
          </button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6 space-y-6">
          <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-2">
            <Sliders className="w-5 h-5 text-blue-500" />
            <h2 className="text-lg font-semibold text-slate-800">Model & Pipeline</h2>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Primary LLM</label>
            <select className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white">
              <option>Gemini 1.5 Pro (Recommended)</option>
              <option>GPT-4o</option>
              <option>Claude 3.5 Sonnet</option>
            </select>
            <p className="text-xs text-slate-500 mt-1">Est. cost: $0.01 / 1k tokens</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Noise Filter Threshold</label>
            <input type="range" min="0" max="100" defaultValue="75" className="w-full accent-blue-600" />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>Lenient</span>
              <span>Strict (75%)</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Chunk Size</label>
              <input type="number" defaultValue={1000} className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Chunk Overlap</label>
              <input type="number" defaultValue={200} className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6 space-y-6">
            <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-2">
              <Database className="w-5 h-5 text-emerald-500" />
              <h2 className="text-lg font-semibold text-slate-800">Vector Database</h2>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Active Provider</label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2">
                  <input type="radio" name="vectordb" value="chroma" defaultChecked className="text-blue-600 focus:ring-blue-500" />
                  <span className="text-sm text-slate-700">ChromaDB (Local/Dev)</span>
                </label>
                <label className="flex items-center gap-2">
                  <input type="radio" name="vectordb" value="pinecone" className="text-blue-600 focus:ring-blue-500" />
                  <span className="text-sm text-slate-700">Pinecone (Prod)</span>
                </label>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6 space-y-6">
            <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-2">
              <Key className="w-5 h-5 text-amber-500" />
              <h2 className="text-lg font-semibold text-slate-800">API Keys & Secrets</h2>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">OpenAI API Key</label>
              <div className="flex gap-2">
                <input type="password" defaultValue="sk-..." className="flex-1 border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-slate-50" readOnly />
                <button className="bg-slate-100 text-slate-700 px-3 py-2 rounded-lg text-sm font-medium hover:bg-slate-200 transition-colors">Edit</button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Pinecone API Key</label>
              <div className="flex gap-2">
                <input type="password" defaultValue="pc-..." className="flex-1 border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-slate-50" readOnly />
                <button className="bg-slate-100 text-slate-700 px-3 py-2 rounded-lg text-sm font-medium hover:bg-slate-200 transition-colors">Edit</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div >
  );
}
