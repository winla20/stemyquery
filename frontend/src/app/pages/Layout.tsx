import { Outlet, Link, useLocation } from "react-router";
import { Microscope, BookOpen } from "lucide-react";

export default function Layout() {
  const location = useLocation();
  const isResearch = location.pathname === "/";
  const isDiscovery = location.pathname === "/discovery";

  return (
    <div className="size-full flex flex-col bg-white">
      <div className="border-b border-slate-200 bg-white">
        <div className="h-16 px-6 flex items-center justify-end">
          <nav className="flex items-center gap-2">
            <Link
              to="/"
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                isResearch
                  ? "bg-slate-100 text-slate-900"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <Microscope className="w-4 h-4" />
              <span className="font-medium">Research Mode</span>
            </Link>
            <Link
              to="/discovery"
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                isDiscovery
                  ? "bg-slate-100 text-slate-900"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span className="font-medium">Discovery Mode</span>
            </Link>
          </nav>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <Outlet />
      </div>
    </div>
  );
}
