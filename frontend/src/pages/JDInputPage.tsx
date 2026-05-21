import { Send } from "lucide-react";

import JDAnalysisPanel from "../components/JDAnalysisPanel";
import { jdProfile } from "../mockData";

export default function JDInputPage() {
  return (
    <main className="mx-auto grid max-w-[1320px] gap-5 px-5 py-6 lg:grid-cols-[0.9fr_1.1fr]">
      <section className="rounded-lg border border-line bg-white p-5 shadow-panel">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
              Input
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-normal">Job description</h2>
          </div>
          <button
            type="button"
            className="inline-flex h-10 items-center gap-2 rounded-md bg-action px-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
          >
            <Send className="h-4 w-4" aria-hidden="true" />
            Analyze
          </button>
        </div>
        <textarea
          className="mt-5 min-h-[520px] w-full resize-none rounded-md border border-line bg-slate-50 p-4 text-sm leading-6 outline-none transition focus:border-action focus:bg-white"
          defaultValue={`Senior Product Data Analyst\n\nOwn funnel metrics, experimentation readouts, and stakeholder-facing reporting for a product-led growth team.`}
        />
      </section>
      <JDAnalysisPanel profile={jdProfile} />
    </main>
  );
}
