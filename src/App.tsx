import { Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import AuthLogin from "./pages/AuthLogin";
import WorkspaceSelector from "./pages/WorkspaceSelector";
import DashboardLayout from "./layouts/DashboardLayout";
import Dashboard from "./pages/Dashboard";
import UploadDocuments from "./pages/UploadDocuments";
import DocumentStatus from "./pages/DocumentStatus";
import DocumentDetail from "./pages/DocumentDetail";
import VectorManager from "./pages/VectorManager";
import QueryChat from "./pages/QueryChat";
import AgentSteps from "./pages/AgentSteps";
import CitationVerifier from "./pages/CitationVerifier";
import QueryHistory from "./pages/QueryHistory";
import TeamAccess from "./pages/TeamAccess";
import AdminDashboard from "./pages/AdminDashboard";
import Settings from "./pages/Settings";

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<AuthLogin />} />
      <Route path="/workspaces" element={<WorkspaceSelector />} />

      {/* Protected Dashboard Routes */}
      <Route element={<DashboardLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<UploadDocuments />} />
        <Route path="/documents/status" element={<DocumentStatus />} />
        <Route path="/documents/:id" element={<DocumentDetail />} />
        <Route path="/vector-manager" element={<VectorManager />} />
        <Route path="/chat" element={<QueryChat />} />
        <Route path="/agent-steps" element={<AgentSteps />} />
        <Route path="/verifier" element={<CitationVerifier />} />
        <Route path="/history" element={<QueryHistory />} />
        <Route path="/team" element={<TeamAccess />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default App;
