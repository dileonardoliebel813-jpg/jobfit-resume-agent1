import { AlertTriangle, CheckCircle2 } from "lucide-react";

import type { MatchAnalysis, UserProfile } from "../types";

interface ExperienceMatchPanelProps {
  profile: UserProfile;
  match: MatchAnalysis;
}

export default function ExperienceMatchPanel({ profile, match }: ExperienceMatchPanelProps) {
  return (
    <section className="h-full rounded-lg border border-line bg-white p-5 shadow-panel">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            Experience Match
          </p>
          <h2 className="mt-2 text-xl font-semibold tracking-normal">{profile.name}</h2>
        </div>
        <div className="text-right">
          <p className="text-3xl font-semibold text-action">
            {Math.round(match.overall_score * 100)}
          </p>
          <p className="text-xs text-slate-500">match score</p>
        </div>
      </div>

      <p className="mt-5 text-sm leading-6 text-slate-700">{profile.headline}</p>

      <div className="mt-6 space-y-4">
        {match.matched_skills.map((item) => (
          <div key={item.skill}>
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">{item.skill}</span>
              <span className="text-slate-500">{Math.round(item.score * 100)}%</span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-slate-100">
              <div
                className="h-2 rounded-full bg-action transition-all"
                style={{ width: `${Math.round(item.score * 100)}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-slate-500">{item.evidence}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <CheckCircle2 className="h-4 w-4 text-action" aria-hidden="true" />
            Recommendations
          </h3>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {match.recommendations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <AlertTriangle className="h-4 w-4 text-amber-500" aria-hidden="true" />
            Gaps
          </h3>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {match.gaps.map((gap) => (
              <li key={gap}>{gap}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
