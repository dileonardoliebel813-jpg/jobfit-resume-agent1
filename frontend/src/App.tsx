import { BarChart3, FileText, Home, PenLine, Sparkles, UserRound } from "lucide-react";
import { useMemo, useState } from "react";

import Dashboard from "./pages/Dashboard";
import JDInputPage from "./pages/JDInputPage";
import MatchAnalysisPage from "./pages/MatchAnalysisPage";
import ProfilePage from "./pages/ProfilePage";
import ResumeEditorPage from "./pages/ResumeEditorPage";

type PageKey = "dashboard" | "jd" | "profile" | "match" | "resume";

const navItems = [
  { key: "dashboard", label: "工作流", icon: Home },
  { key: "jd", label: "JD 分析", icon: FileText },
  { key: "profile", label: "个人信息", icon: UserRound },
  { key: "match", label: "匹配诊断", icon: BarChart3 },
  { key: "resume", label: "简历编辑", icon: PenLine },
] satisfies Array<{ key: PageKey; label: string; icon: typeof Home }>;

export default function App() {
  const [page, setPage] = useState<PageKey>("dashboard");

  const pageTitle = useMemo(
    () => navItems.find((item) => item.key === page)?.label ?? "Dashboard",
    [page],
  );

  return (
    <div className="min-h-screen text-ink">
      <header className="sticky top-0 z-40 border-b border-white/70 bg-white/80 shadow-[0_12px_35px_rgba(15,23,42,0.06)] backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1520px] flex-col gap-4 px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-action to-cyan-500 text-white shadow-lg shadow-teal-600/20">
              <Sparkles className="h-6 w-6" aria-hidden="true" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-action">
                JobFit Resume Agent
              </p>
              <h1 className="mt-1 text-xl font-bold tracking-tight text-slate-950 md:text-2xl">
                正式简历生成 · {pageTitle}
              </h1>
            </div>
          </div>
          <nav className="flex flex-wrap gap-2 rounded-full border border-slate-200/80 bg-white/70 p-1 shadow-sm">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.key === page;
              return (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => setPage(item.key)}
                  className={`inline-flex h-10 items-center gap-2 rounded-full px-4 text-sm font-bold transition focus:outline-none focus:ring-4 focus:ring-teal-100 ${
                    isActive
                      ? "bg-slate-950 text-white shadow-md shadow-slate-900/15"
                      : "text-slate-600 hover:bg-teal-50 hover:text-action"
                  }`}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {page === "dashboard" && <Dashboard />}
      {page === "jd" && <JDInputPage />}
      {page === "profile" && <ProfilePage />}
      {page === "match" && <MatchAnalysisPage />}
      {page === "resume" && <ResumeEditorPage />}
    </div>
  );
}
