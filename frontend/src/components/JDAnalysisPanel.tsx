import { BadgeCheck, BriefcaseBusiness, ListChecks, Sparkles } from "lucide-react";

import type { JDProfile } from "../types";

interface JDAnalysisPanelProps {
  profile: JDProfile;
}

interface SectionProps {
  title: string;
  items: string[];
  variant?: "list" | "tag";
}

function Section({ title, items, variant = "list" }: SectionProps) {
  if (!items.length) {
    return null;
  }

  return (
    <div className="border-t border-slate-100 pt-4">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      {variant === "tag" ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {items.map((item) => (
            <span
              key={item}
              className="rounded-lg border border-teal-100 bg-teal-50 px-2.5 py-1 text-xs font-medium text-teal-800"
            >
              {item}
            </span>
          ))}
        </div>
      ) : (
        <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700">
          {items.map((item) => (
            <li key={item} className="flex gap-2">
              <BadgeCheck className="mt-1 h-4 w-4 flex-none text-action" aria-hidden="true" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function JDAnalysisPanel({ profile }: JDAnalysisPanelProps) {
  return (
    <section className="h-full rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            2. 岗位画像分析
          </p>
          <h2 className="mt-3 text-2xl font-semibold tracking-normal text-slate-950">
            {profile.position}
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
              {profile.job_level}
            </span>
            <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
              {profile.job_type}
            </span>
          </div>
        </div>
        <div className="rounded-xl bg-teal-50 p-2 text-action">
          <BriefcaseBusiness className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>

      <div className="mt-5 rounded-2xl bg-slate-50 p-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
          <Sparkles className="h-4 w-4 text-action" aria-hidden="true" />
          语气策略
        </div>
        <p className="mt-2 text-sm leading-6 text-slate-700">{profile.resume_strategy.tone}</p>
      </div>

      <div className="mt-5 space-y-5">
        <Section title="硬性要求" items={profile.hard_requirements} />
        <Section title="核心职责" items={profile.core_tasks} />
        <Section title="必备技能" items={profile.required_skills} variant="tag" />
        <Section title="加分经历" items={profile.preferred_experience} />
        <Section title="隐性偏好" items={profile.hidden_preferences} />
        <Section title="简历策略：必须突出" items={profile.resume_strategy.must_highlight} />
        <Section title="应弱化内容" items={profile.resume_strategy.should_weaken} />
      </div>

      <div className="mt-5 flex items-center gap-2 rounded-2xl border border-teal-100 bg-teal-50 px-4 py-3 text-sm font-medium text-teal-900">
        <ListChecks className="h-4 w-4" aria-hidden="true" />
        已生成可用于匹配、证据约束和 ATS 优化的岗位画像。
      </div>
    </section>
  );
}
