import { BarChart3, FileText, Home, PenLine, UserRound } from "lucide-react";
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
    <div className="min-h-screen bg-mist text-ink">
      <header className="sticky top-0 z-40 border-b border-line bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1520px] flex-col gap-4 px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-action">
              JobFit Resume Agent
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-normal">正式简历生成 · {pageTitle}</h1>
          </div>
          <nav className="flex flex-wrap gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.key === page;
              return (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => setPage(item.key)}
                  className={`inline-flex h-10 items-center gap-2 rounded-md border px-3 text-sm font-medium transition ${
                    isActive
                      ? "border-action bg-action text-white"
                      : "border-line bg-white text-slate-600 hover:border-action hover:text-action"
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
