from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.jd_schema import JDProfile
from app.schemas.profile_schema import UserProfile


class SkillMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill: str
    score: float
    evidence: str


class MatchAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_score: float
    matched_skills: list[SkillMatch]
    gaps: list[str]
    recommendations: list[str]


EvidenceStatus = Literal[
    "direct_evidence",
    "weak_evidence",
    "missing_evidence",
    "user_confirmed_absent",
]
GenerationRecommendation = Literal["ready", "needs_more_info", "not_recommended"]


class EvidenceDiagnosisItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str
    category: str
    status: EvidenceStatus
    matched_experience: str
    evidence_snippet: str
    confidence: float
    suggestion: str


class MissingEvidenceQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str
    question: str
    reason: str


class SafeResumeStrategy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    can_write: list[str]
    should_weaken: list[str]
    must_not_claim: list[str]


class MatchDiagnoseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jd_profile: JDProfile
    user_profile: UserProfile
    raw_profile_text: str | None = None
    user_confirmed_absent_requirements: list[str] = Field(default_factory=list)


class MatchDiagnoseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coverage_score: float
    generation_recommendation: GenerationRecommendation
    evidence_items: list[EvidenceDiagnosisItem]
    missing_evidence_questions: list[MissingEvidenceQuestion]
    safe_resume_strategy: SafeResumeStrategy


class MatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jd_profile: JDProfile
    user_profile: UserProfile


class MatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    match: MatchAnalysis
