import { Link, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  UploadCloud,
  FileText,
  Database,
  MessageSquare,
  Activity,
  CheckCircle,
  History,
  Users,
  Settings,
  ShieldAlert,
} from "lucide-react";

export default function DashboardLayout() {
  const location = useLocation();

  const navItems = [
    { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { name: "Upload Documents", path: "/upload", icon: UploadCloud },
    { name: "Processing Status", path: "/documents/status", icon: Activity },
    { name: "Vector Manager", path: "/vector-manager", icon: Database },
    { name: "Query Chat", path: "/chat", icon: MessageSquare },
    { name: "Agent Steps", path: "/agent-steps", icon: Activity },
    { name: "Citation Verifier", path: "/verifier", icon: CheckCircle },
    { name: "History", path: "/history", icon: History },
    { name: "Team Access", path: "/team", icon: Users },
    { name: "Admin", path: "/admin", icon: ShieldAlert },
    { name: "Settings", path: "/settings", icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col">
        <div className="p-4 border-b border-slate-800">
          <h1 className="text-xl font-bold text-white tracking-tight">
            FAR Copilot
          </h1>
          <p className="text-xs text-slate-500 mt-1">Gov Consulting Platform</p>
        </div>

        <nav className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                location.pathname === item.path ||
                location.pathname.startsWith(item.path + "/");
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                      isActive
                        ? "bg-blue-600 text-white"
                        : "hover:bg-slate-800 hover:text-white"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{item.name}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-white font-bold text-sm">
              JD
            </div>
            <div>
              <p className="text-sm font-medium text-white">Jane Doe</p>
              <p className="text-xs text-slate-500">Admin</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 shadow-sm z-10">
          <div className="font-medium text-slate-800">
            {navItems.find((i) => location.pathname.startsWith(i.path))?.name ||
              "Workspace"}
          </div>
          <div className="flex items-center gap-4">
            <Link
              to="/workspaces"
              className="text-sm text-slate-500 hover:text-slate-800"
            >
              Switch Workspace
            </Link>
            <Link
              to="/"
              className="text-sm text-slate-500 hover:text-slate-800"
            >
              Sign Out
            </Link>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
