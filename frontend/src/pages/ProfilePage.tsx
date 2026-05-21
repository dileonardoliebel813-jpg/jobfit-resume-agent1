import { Upload } from "lucide-react";

import { userProfile } from "../mockData";

export default function ProfilePage() {
  return (
    <main className="mx-auto grid max-w-[1320px] gap-5 px-5 py-6 lg:grid-cols-[0.9fr_1.1fr]">
      <section className="rounded-lg border border-line bg-white p-5 shadow-panel">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
              Profile Source
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-normal">Experience text</h2>
          </div>
          <button
            type="button"
            className="inline-flex h-10 items-center gap-2 rounded-md bg-action px-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
          >
            <Upload className="h-4 w-4" aria-hidden="true" />
            Parse
          </button>
        </div>
        <textarea
          className="mt-5 min-h-[520px] w-full resize-none rounded-md border border-line bg-slate-50 p-4 text-sm leading-6 outline-none transition focus:border-action focus:bg-white"
          defaultValue="Product analyst with SQL, Python, funnel analytics, experiment readouts, dashboards, and stakeholder reporting experience."
        />
      </section>
      <section className="rounded-lg border border-line bg-white p-5 shadow-panel">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
          Parsed Profile
        </p>
        <h2 className="mt-2 text-xl font-semibold tracking-normal">{userProfile.name}</h2>
        <p className="mt-3 text-sm leading-6 text-slate-700">{userProfile.headline}</p>
        <div className="mt-6 space-y-5">
          {userProfile.experiences.map((experience) => (
            <article key={`${experience.company}-${experience.role}`} className="border-t border-line pt-4">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="font-semibold">{experience.role}</h3>
                <span className="text-xs text-slate-500">{experience.duration}</span>
              </div>
              <p className="mt-1 text-sm text-slate-600">{experience.company}</p>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
                {experience.highlights.map((highlight) => (
                  <li key={highlight}>{highlight}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
