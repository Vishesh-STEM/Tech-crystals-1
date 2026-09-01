import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3, BookOpen, Bot, GraduationCap, LayoutDashboard, ListChecks, LogOut, Menu,
  Moon, Settings as SettingsIcon, Sparkles, Sun, User as UserIcon, Users, X, FileQuestion,
  Layers, Library, ClipboardList, TrendingUp,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { endpoints } from "../lib/api";

const studentNav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/subjects", label: "Subjects", icon: BookOpen },
  { to: "/quizzes", label: "Quizzes", icon: ClipboardList },
  { to: "/chat", label: "AI Tutor", icon: Bot },
  { to: "/recommendations", label: "For you", icon: ListChecks },
  { to: "/progress", label: "Progress", icon: TrendingUp },
];

const adminNav = [
  { to: "/admin", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/admin/students", label: "Students", icon: Users },
  { to: "/admin/subjects", label: "Subjects", icon: Library },
  { to: "/admin/chapters", label: "Chapters", icon: Layers },
  { to: "/admin/topics", label: "Topics", icon: BookOpen },
  { to: "/admin/resources", label: "Resources", icon: FileQuestion },
  { to: "/admin/questions", label: "Questions", icon: FileQuestion },
  { to: "/admin/quizzes", label: "Quizzes", icon: ClipboardList },
  { to: "/admin/analytics", label: "Analytics", icon: BarChart3 },
];

export default function Layout() {
  const { user, logout, academicYear } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [aiMode, setAiMode] = useState<string>("");

  const isStaff = user?.role === "teacher" || user?.role === "admin";
  const items = location.pathname.startsWith("/admin") ? adminNav : studentNav;

  useEffect(() => setOpen(false), [location.pathname]);

  useEffect(() => {
    let cancelled = false;
    endpoints
      .meta()
      .then((meta) => {
        if (!cancelled) setAiMode(meta?.ai?.mode ?? "");
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-ink-50 dark:bg-ink-950">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[260px] transform border-r border-ink-200/70 bg-white transition-transform duration-200 dark:border-white/10 dark:bg-ink-900 lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-16 items-center gap-2.5 border-b border-ink-200/70 px-5 dark:border-white/10">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-violet-500 text-white shadow-lift">
            <GraduationCap size={20} />
          </div>
          <div className="min-w-0">
            <p className="font-display text-[15px] font-semibold leading-tight text-ink-900 dark:text-white">
              Vidyalaya AI
            </p>
            <p className="truncate text-[11px] text-ink-500 dark:text-ink-400">Learn smarter. Study what matters.</p>
          </div>
          <button className="ml-auto lg:hidden" onClick={() => setOpen(false)} aria-label="Close menu">
            <X size={18} />
          </button>
        </div>

        <nav className="flex flex-col gap-1 p-3">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={(item as any).end}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                    isActive
                      ? "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-200"
                      : "text-ink-600 hover:bg-ink-100 dark:text-ink-300 dark:hover:bg-white/5"
                  }`
                }
              >
                <Icon size={18} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        {isStaff ? (
          <div className="px-3">
            <Link
              to={location.pathname.startsWith("/admin") ? "/dashboard" : "/admin"}
              className="btn-secondary w-full justify-start"
            >
              <Users size={16} />
              {location.pathname.startsWith("/admin") ? "Student view" : "Teacher workspace"}
            </Link>
          </div>
        ) : null}

        <div className="absolute inset-x-0 bottom-0 border-t border-ink-200/70 p-3 dark:border-white/10">
          <div className="mb-2 flex items-center gap-2 rounded-xl bg-ink-50 px-3 py-2 dark:bg-white/5">
            <Sparkles size={15} className={aiMode === "ollama" ? "text-emerald-500" : "text-amber-500"} />
            <span className="text-xs text-ink-600 dark:text-ink-300">
              {aiMode === "ollama" ? "AI tutor: local model" : "AI tutor: offline mode"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Link to="/profile" className="flex min-w-0 flex-1 items-center gap-2 rounded-xl px-2 py-2 hover:bg-ink-100 dark:hover:bg-white/5">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-brand-100 text-sm dark:bg-brand-500/20">
                {user?.avatar_emoji || "🎓"}
              </span>
              <span className="min-w-0">
                <span className="block truncate text-sm font-medium text-ink-800 dark:text-ink-100">
                  {user?.full_name}
                </span>
                <span className="block truncate text-[11px] text-ink-500 dark:text-ink-400">
                  {academicYear ? `Class 12 · ${academicYear}` : user?.role}
                </span>
              </span>
            </Link>
            <button
              className="btn-ghost px-2"
              onClick={() => {
                logout();
                navigate("/login");
              }}
              aria-label="Log out"
              title="Log out"
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>

      {open ? (
        <div className="fixed inset-0 z-30 bg-ink-900/40 backdrop-blur-sm lg:hidden" onClick={() => setOpen(false)} />
      ) : null}

      {/* Main */}
      <div className="lg:pl-[260px]">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-ink-200/70 bg-white/80 px-4 backdrop-blur dark:border-white/10 dark:bg-ink-900/80 sm:px-6">
          <button className="btn-ghost px-2 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
            <Menu size={20} />
          </button>
          <div className="min-w-0 flex-1">
            <p className="truncate font-display text-base font-semibold text-ink-900 dark:text-white">
              {items.find((item) => location.pathname === item.to)?.label ?? "Vidyalaya AI"}
            </p>
          </div>
          <Link to="/chat" className="btn-ghost hidden sm:inline-flex" title="Ask the AI tutor">
            <Bot size={18} /> Ask AI
          </Link>
          <button className="btn-ghost px-2" onClick={toggle} aria-label="Toggle theme" title="Toggle theme">
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <Link to="/settings" className="btn-ghost px-2" aria-label="Settings" title="Settings">
            <SettingsIcon size={18} />
          </Link>
        </header>
        <main className="mx-auto max-w-[1200px] animate-fade-up px-4 py-6 sm:px-6 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
