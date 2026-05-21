from app.schemas.evidence_schema import EvidenceItem
from app.schemas.jd_schema import JDProfile
from app.schemas.profile_schema import UserProfile


class EvidenceBuilderAgent:
    def build(self, jd_profile: JDProfile, user_profile: UserProfile) -> list[EvidenceItem]:
        evidence: list[EvidenceItem] = []
        requirements = [*jd_profile.hard_requirements, *jd_profile.required_skills]

        for requirement in dict.fromkeys(requirements):
            matched_experience = "未匹配到直接证据"
            snippet = "候选人经历中未发现直接证据"
            confidence = 0.0

            for experience in user_profile.experiences:
                searchable = " ".join(
                    [
                        experience.role,
                        *experience.highlights,
                        *experience.skills,
                    ]
                ).lower()
                requirement_terms = [
                    term.lower()
                    for term in [requirement, *requirement.replace("、", " ").split()]
                    if term.strip()
                ]
                if any(term in searchable for term in requirement_terms):
                    matched_experience = experience.role
                    snippet = experience.highlights[0] if experience.highlights else experience.role
                    confidence = 0.82
                    break

            evidence.append(
                EvidenceItem(
                    requirement=requirement,
                    matched_experience=matched_experience,
                    evidence_snippet=snippet,
                    confidence=confidence,
                )
            )

        return evidence[:8]
