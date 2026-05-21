import re
from dataclasses import dataclass

from app.schemas.jd_schema import JDProfile
from app.schemas.match_schema import (
    EvidenceDiagnosisItem,
    MatchDiagnoseResponse,
    MissingEvidenceQuestion,
    SafeResumeStrategy,
)
from app.schemas.profile_schema import UserProfile, WorkExperience


@dataclass(frozen=True)
class Requirement:
    text: str
    category: str


class EvidenceGuidanceAgent:
    """Builds conservative evidence diagnostics before resume generation."""

    _GENERIC_TERMS = {
        "能力",
        "经验",
        "相关",
        "负责",
        "进行",
        "完成",
        "熟悉",
        "具备",
        "要求",
        "岗位",
    }
    _RELATED_GROUPS = (
        {"产品", "需求", "PRD", "原型", "用户", "竞品", "版本", "迭代", "Axure", "Figma"},
        {"数据", "指标", "SQL", "Python", "分析", "看板", "埋点", "统计", "建模"},
        {"AI", "AIGC", "大模型", "LLM", "RAG", "Prompt", "向量", "推荐", "算法"},
        {"协作", "研发", "设计", "测试", "运营", "沟通", "推进", "项目管理"},
    )

    def diagnose(
        self,
        jd_profile: JDProfile,
        user_profile: UserProfile,
        raw_profile_text: str | None = None,
        user_confirmed_absent_requirements: list[str] | None = None,
    ) -> MatchDiagnoseResponse:
        absent = set(user_confirmed_absent_requirements or [])
        requirements = self._requirements(jd_profile)
        evidence_items = [
            self._diagnose_requirement(item, user_profile, raw_profile_text or "", absent)
            for item in requirements
        ]

        direct = [item.requirement for item in evidence_items if item.status == "direct_evidence"]
        weak = [item.requirement for item in evidence_items if item.status == "weak_evidence"]
        blocked = [
            item.requirement
            for item in evidence_items
            if item.status in {"missing_evidence", "user_confirmed_absent"}
        ]
        coverage_score = self._coverage_score(evidence_items)
        questions = self._missing_questions(evidence_items)

        return MatchDiagnoseResponse(
            coverage_score=coverage_score,
            generation_recommendation=self._recommend_generation(
                coverage_score,
                direct_count=len(direct),
                has_experience=bool(user_profile.experiences),
            ),
            evidence_items=evidence_items,
            missing_evidence_questions=questions,
            safe_resume_strategy=SafeResumeStrategy(
                can_write=direct,
                should_weaken=weak,
                must_not_claim=blocked,
            ),
        )

    def _requirements(self, jd_profile: JDProfile) -> list[Requirement]:
        grouped = [
            ("硬性要求", jd_profile.hard_requirements),
            ("核心职责", jd_profile.core_tasks),
            ("必备技能", jd_profile.required_skills),
            ("加分经历", jd_profile.preferred_experience),
        ]
        seen: set[str] = set()
        requirements: list[Requirement] = []
        for category, values in grouped:
            for value in values:
                normalized = value.strip()
                if normalized and normalized not in seen:
                    requirements.append(Requirement(text=normalized, category=category))
                    seen.add(normalized)
        return requirements[:14]

    def _diagnose_requirement(
        self,
        requirement: Requirement,
        user_profile: UserProfile,
        raw_profile_text: str,
        absent: set[str],
    ) -> EvidenceDiagnosisItem:
        if requirement.text in absent:
            return EvidenceDiagnosisItem(
                requirement=requirement.text,
                category=requirement.category,
                status="user_confirmed_absent",
                matched_experience="用户确认没有相关经历",
                evidence_snippet="用户已明确选择没有这项相关经历",
                confidence=0.0,
                suggestion="不要把这项要求写入简历，可在求职策略中作为差距处理。",
            )

        terms = self._terms(requirement.text)
        best_experience, best_score = self._best_experience(terms, user_profile.experiences)
        source_text = self._source_text(user_profile, raw_profile_text)
        exact_match = any(self._contains(source_text, term) for term in terms)

        if exact_match and best_score >= 1:
            snippet = self._snippet(best_experience, terms) if best_experience else requirement.text
            return EvidenceDiagnosisItem(
                requirement=requirement.text,
                category=requirement.category,
                status="direct_evidence",
                matched_experience=best_experience.role if best_experience else "个人经历文本",
                evidence_snippet=snippet,
                confidence=0.82,
                suggestion="可以写入简历，但表达必须绑定这条真实经历。",
            )

        if self._has_related_group_overlap(requirement.text, source_text) or best_score > 0:
            snippet = self._snippet(best_experience, terms) if best_experience else "存在弱相关信息，但缺少直接证据"
            return EvidenceDiagnosisItem(
                requirement=requirement.text,
                category=requirement.category,
                status="weak_evidence",
                matched_experience=best_experience.role if best_experience else "个人经历文本",
                evidence_snippet=snippet,
                confidence=0.42,
                suggestion="只能弱化表达，建议补充项目名称、职责、工具、产出或指标。",
            )

        return EvidenceDiagnosisItem(
            requirement=requirement.text,
            category=requirement.category,
            status="missing_evidence",
            matched_experience="未匹配到直接证据",
            evidence_snippet="候选人经历中未发现可验证证据",
            confidence=0.0,
            suggestion="生成简历前应补充真实经历；如果确实没有，请选择“没有”。",
        )

    def _terms(self, requirement: str) -> list[str]:
        pieces = re.split(r"[\s,，、;；/()（）:：]+", requirement)
        terms = []
        for piece in pieces:
            value = piece.strip()
            if len(value) >= 2 and value not in self._GENERIC_TERMS:
                terms.append(value)
        if requirement.strip():
            terms.append(requirement.strip())
        return list(dict.fromkeys(terms))

    def _best_experience(
        self,
        terms: list[str],
        experiences: list[WorkExperience],
    ) -> tuple[WorkExperience | None, int]:
        best: WorkExperience | None = None
        best_score = 0
        for experience in experiences:
            text = " ".join(
                [experience.company, experience.role, experience.duration, *experience.highlights, *experience.skills]
            )
            score = sum(1 for term in terms if term and self._contains(text, term))
            if score > best_score:
                best = experience
                best_score = score
        return best, best_score

    def _source_text(self, user_profile: UserProfile, raw_profile_text: str) -> str:
        return " ".join(
            [
                raw_profile_text,
                user_profile.name,
                user_profile.headline,
                *user_profile.skills,
                *user_profile.education,
                *[
                    " ".join(
                        [
                            experience.company,
                            experience.role,
                            experience.duration,
                            *experience.highlights,
                            *experience.skills,
                        ]
                    )
                    for experience in user_profile.experiences
                ],
            ]
        )

    def _has_related_group_overlap(self, requirement: str, source_text: str) -> bool:
        for group in self._RELATED_GROUPS:
            if any(self._contains(requirement, term) for term in group) and any(
                self._contains(source_text, term) for term in group
            ):
                return True
        return False

    def _snippet(self, experience: WorkExperience | None, terms: list[str]) -> str:
        if experience is None:
            return "个人经历文本中存在相关信息"
        for highlight in experience.highlights:
            if any(self._contains(highlight, term) for term in terms):
                return highlight
        if experience.highlights:
            return experience.highlights[0]
        return experience.role

    def _contains(self, text: str, term: str) -> bool:
        return term.casefold() in text.casefold()

    def _coverage_score(self, items: list[EvidenceDiagnosisItem]) -> float:
        if not items:
            return 0.0
        score = sum(item.confidence for item in items) / len(items)
        return round(score, 2)

    def _recommend_generation(
        self,
        coverage_score: float,
        direct_count: int,
        has_experience: bool,
    ) -> str:
        if not has_experience or coverage_score < 0.15 or direct_count == 0:
            return "not_recommended"
        if coverage_score >= 0.55 and direct_count >= 3:
            return "ready"
        return "needs_more_info"

    def _missing_questions(
        self,
        items: list[EvidenceDiagnosisItem],
    ) -> list[MissingEvidenceQuestion]:
        questions: list[MissingEvidenceQuestion] = []
        for item in items:
            if item.status not in {"missing_evidence", "weak_evidence"}:
                continue
            questions.append(
                MissingEvidenceQuestion(
                    requirement=item.requirement,
                    question=(
                        f"你是否真实做过与“{item.requirement}”相关的事情？"
                        "如果有，请补充项目名称、你的角色、具体动作、使用工具、产出或指标；"
                        "如果没有，请明确选择没有。"
                    ),
                    reason=item.suggestion,
                )
            )
        return questions[:8]
