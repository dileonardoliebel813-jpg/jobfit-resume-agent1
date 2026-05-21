import { ShieldCheck } from "lucide-react";

import type { FactCheckResult } from "../types";

interface FactCheckPanelProps {
  result: FactCheckResult;
}

export default function FactCheckPanel({ result }: FactCheckPanelProps) {
  return (
    <section className="rounded-lg border border-line bg-white p-5 shadow-panel">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            Fact Check
          </p>
          <p className="mt-2 text-sm text-slate-700">{result.summary}</p>
        </div>
        <ShieldCheck className="h-5 w-5 text-action" aria-hidden="true" />
      </div>
      <div className="mt-4 space-y-3">
        {result.items.map((item) => (
          <div key={item.claim} className="border-t border-line pt-3">
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs font-medium uppercase tracking-[0.12em] text-amber-600">
                {item.status}
              </span>
              <span className="text-xs text-slate-500">{item.source_hint}</span>
            </div>
            <p className="mt-2 text-sm text-slate-700">{item.note}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
