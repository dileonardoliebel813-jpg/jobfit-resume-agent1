import ATSScoreCard from "../components/ATSScoreCard";
import ExportButton from "../components/ExportButton";
import FactCheckPanel from "../components/FactCheckPanel";
import ResumePreview from "../components/ResumePreview";
import { atsReview, factCheck, resumeJson } from "../mockData";

export default function ResumeEditorPage() {
  return (
    <main className="mx-auto grid max-w-[1320px] gap-5 px-5 py-6 lg:grid-cols-[1.25fr_0.75fr]">
      <ResumePreview resume={resumeJson} />
      <aside className="space-y-5">
        <ATSScoreCard review={atsReview} />
        <FactCheckPanel result={factCheck} />
        <ExportButton resume={resumeJson} />
      </aside>
    </main>
  );
}
