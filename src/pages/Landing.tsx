import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
      <header className="flex items-center justify-between px-8 py-6 max-w-7xl mx-auto w-full">
        <div className="text-2xl font-bold tracking-tight text-slate-900">FAR Copilot</div>
        <nav className="flex gap-6 items-center">
          <a href="#how-it-works" className="text-slate-600 hover:text-slate-900 font-medium">How it works</a>
          <a href="#pricing" className="text-slate-600 hover:text-slate-900 font-medium">Pricing</a>
          <Link to="/login" className="text-slate-600 hover:text-slate-900 font-medium">Log in</Link>
          <Link to="/login" className="bg-blue-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition-colors">
            Try Demo
          </Link>
        </nav>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center text-center px-4 max-w-4xl mx-auto py-20">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 mb-6 leading-tight">
          Predictive Compliance Intelligence
        </h1>
        <p className="text-xl text-slate-600 mb-10 max-w-2xl leading-relaxed">
          Upload your RFPs and regulations. Get instant, citation-backed answers verified by AI. The ultimate platform for federal contractors.
        </p>
        <div className="flex flex-col sm:flex-row gap-4">
          <Link to="/login" className="bg-blue-600 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:bg-blue-700 transition-colors shadow-lg shadow-blue-600/20">
            Start Free Trial
          </Link>
          <button className="bg-white text-slate-800 border border-slate-200 px-8 py-4 rounded-xl font-semibold text-lg hover:bg-slate-50 transition-colors shadow-sm">
            Book a Demo
          </button>
        </div>

        <div className="mt-24 grid md:grid-cols-3 gap-8 text-left w-full">
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100">
            <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center font-bold text-xl mb-6">1</div>
            <h3 className="text-xl font-bold mb-3">Upload Documents</h3>
            <p className="text-slate-600 leading-relaxed">Securely ingest PDFs, DOCX, and TXT files. We parse, chunk, and index them instantly.</p>
          </div>
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100">
            <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center font-bold text-xl mb-6">2</div>
            <h3 className="text-xl font-bold mb-3">Ask Questions</h3>
            <p className="text-slate-600 leading-relaxed">Query your documents using natural language. Get answers backed by exact citations.</p>
          </div>
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100">
            <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center font-bold text-xl mb-6">3</div>
            <h3 className="text-xl font-bold mb-3">Verify & Export</h3>
            <p className="text-slate-600 leading-relaxed">Review the AI's reasoning, check source snippets, and export compliance reports.</p>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-200 py-12 text-center text-slate-500 mt-auto">
        <p>© 2026 FAR Copilot. All rights reserved.</p>
      </footer>
    </div>
  );
}
