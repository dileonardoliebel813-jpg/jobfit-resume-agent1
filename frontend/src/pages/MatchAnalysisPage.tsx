import ExperienceMatchPanel from "../components/ExperienceMatchPanel";
import JDAnalysisPanel from "../components/JDAnalysisPanel";
import { jdProfile, matchAnalysis, userProfile } from "../mockData";

export default function MatchAnalysisPage() {
  return (
    <main className="mx-auto grid max-w-[1320px] gap-5 px-5 py-6 lg:grid-cols-[0.95fr_1.05fr]">
      <JDAnalysisPanel profile={jdProfile} />
      <ExperienceMatchPanel profile={userProfile} match={matchAnalysis} />
    </main>
  );
}
