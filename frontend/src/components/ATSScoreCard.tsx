import { Gauge } from "lucide-react";

import type { ATSReviewResult } from "../types";

interface ATSScoreCardProps {
  review: ATSReviewResult;
}

export default function ATSScoreCard({ review }: ATSScoreCardProps) {
  return (
    <section className="rounded-lg border border-line bg-white p-5 shadow-panel">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            ATS Review
          </p>
          <p className="mt-2 text-sm text-slate-700">{review.summary}</p>
        </div>
        <Gauge className="h-5 w-5 text-action" aria-hidden="true" />
      </div>
      <div className="mt-5 flex items-end gap-3">
        <span className="text-4xl font-semibold text-action">{review.score}</span>
        <span className="pb-1 text-sm text-slate-500">
          {Math.round(review.keyword_coverage * 100)}% keywords
        </span>
      </div>
    </section>
  );
}
