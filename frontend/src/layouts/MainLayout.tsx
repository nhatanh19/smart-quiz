import React from "react";
import { useAuth } from "@/contexts/AuthContext";
import { canManageExams } from "@/lib/permissions";
import AuthAction from "@/pages/auth/AuthAction";
import { Link, NavLink, Outlet } from "react-router-dom";
import { BookOpen, Sparkles, GraduationCap, BarChart2 } from "lucide-react";

/**
 * MainLayout:
 * Global application shell with standard navigation header and main content area with <Outlet />.
 */
export const MainLayout: React.FC = () => {
  const { user } = useAuth();
  const manager = !!user && canManageExams(user.role);
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      {/* Top Header Navigation */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 min-h-16 py-3 flex flex-wrap gap-3 items-center justify-between">
          {/* Logo & Project Title */}
          <Link to="/" className="flex items-center gap-2 font-bold text-xl text-primary">
            <span className="text-2xl">🧠</span>
            <span>Smart Quiz</span>
            <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium ml-1">
              Boilerplate
            </span>
          </Link>

          {/* Module Navigation Links */}
          <nav aria-label="Điều hướng chính" className="flex flex-wrap items-center gap-1 sm:gap-2">
            <NavLink to="/profile" className="px-3 py-1.5 text-sm font-medium text-blue-700">Hồ sơ cá nhân</NavLink>
            {manager && <>
            <NavLink to="/instructor/exams" className="px-3 py-1.5 text-sm font-medium text-blue-700">Ca thi</NavLink>
            <NavLink
              to="/instructor/parser"
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-white"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`
              }
            >
              <BookOpen className="w-4 h-4" />
              <span>Parser (M1)</span>
            </NavLink>

            <NavLink
              to="/instructor/ai-generator"
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-white"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`
              }
            >
              <Sparkles className="w-4 h-4" />
              <span>AI Gen (M2)</span>
            </NavLink>

            </>}
            <NavLink
              to={manager ? "/instructor/exams" : "/exam/join"}
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-white"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`
              }
            >
              <GraduationCap className="w-4 h-4" />
              <span>Exam (M3)</span>
            </NavLink>

            {manager && <NavLink
              to="/instructor/analytics"
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-white"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`
              }
            >
              <BarChart2 className="w-4 h-4" />
              <span>Analytics (M4)</span>
            </NavLink>}
          </nav>

          {/* Auth Action */}
          <div className="flex items-center gap-3">
            <AuthAction />
          </div>
        </div>
      </header>

      {/* Main Workspace Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        <Outlet />
      </main>

      {/* Footer Note */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        Smart Quiz Boilerplate Platform • Quản trị Dự án Phần mềm
      </footer>
    </div>
  );
};

export default MainLayout;
