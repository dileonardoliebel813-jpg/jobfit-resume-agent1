from app.schemas.evidence_schema import EvidenceItem
from app.schemas.jd_schema import JDProfile
from app.schemas.match_schema import MatchAnalysis, SkillMatch
from app.schemas.profile_schema import UserProfile


class HybridMatchAgent:
    def match(
        self,
        jd_profile: JDProfile,
        user_profile: UserProfile,
        evidence: list[EvidenceItem],
    ) -> MatchAnalysis:
        user_text = " ".join(
            [
                *user_profile.skills,
                *[
                    " ".join([experience.role, *experience.highlights, *experience.skills])
                    for experience in user_profile.experiences
                ],
            ]
        ).lower()
        matched_skills: list[SkillMatch] = []

        for skill in jd_profile.required_skills:
            normalized = skill.lower()
            has_direct_evidence = normalized in user_text
            score = 0.9 if has_direct_evidence else 0.0
            matched_skills.append(
                SkillMatch(
                    skill=skill,
                    score=score,
                    evidence=(
                        "候选人经历中存在直接证据"
                        if has_direct_evidence
                        else "候选人经历中未发现直接证据"
                    ),
                )
            )

        gaps = [
            skill
            for skill in jd_profile.required_skills
            if skill.lower() not in user_text
        ]
        scored_items = matched_skills or [
            SkillMatch(skill="暂无匹配技能", score=0.0, evidence="候选人经历中未发现直接证据")
        ]
        overall_score = sum(item.score for item in scored_items) / len(scored_items)

        return MatchAnalysis(
            overall_score=round(overall_score, 2),
            matched_skills=matched_skills[:8],
            gaps=gaps,
            recommendations=[
                "只突出候选人经历中已有证据支持的能力。",
                "对未发现证据的 JD 要求，先补充真实经历再写入简历。",
                f"本次匹配使用了 {len([item for item in evidence if item.confidence > 0])} 条直接证据。",
            ],
        )
