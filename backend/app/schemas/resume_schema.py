from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.evidence_schema import EvidenceItem
from app.schemas.jd_schema import JDProfile
from app.schemas.match_schema import GenerationRecommendation, MatchAnalysis
from app.schemas.profile_schema import UserProfile


ResumeEvidenceStatus = Literal[
    "supported",
    "transferable",
    "inferred",
    "unsupported",
    "missing",
]


class ResumeBullet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    evidence_status: ResumeEvidenceStatus
    risk_level: Literal["low", "medium", "high"] = "low"


class ResumeModule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    subtitle: str = ""
    bullets: list[ResumeBullet]


class ResumeSideReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    missing_info: list[str]
    weak_match_points: list[str]
    suggested_user_inputs: list[str]
    assumptions_need_confirmation: list[str]
    match_gap_summary: str


class ResumeJSON(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_name: str
    target_title: str
    headline: str
    summary: list[ResumeBullet]
    skills: list[str]
    projects: list[ResumeModule]
    practice_experiences: list[ResumeModule]
    campus_or_competition: list[ResumeModule]
    education: list[str]
    self_evaluation: list[ResumeBullet]
    side_report: ResumeSideReport


class ResumeGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jd_profile: JDProfile
    user_profile: UserProfile


class ResumeGenerateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resume_json: ResumeJSON
    match: MatchAnalysis
    evidence: list[EvidenceItem]
    strategy_notes: list[str]
    coverage_score: float
    missing_fields: list[str]
    generation_recommendation: GenerationRecommendation


class ResumeReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resume_json: ResumeJSON
    jd_profile: JDProfile | None = None
    user_profile: UserProfile | None = None


class FactCheckItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: str
    status: ResumeEvidenceStatus
    source_hint: str
    note: str


class FactCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_level: Literal["low", "medium", "high"]
    summary: str
    items: list[FactCheckItem]


class FactCheckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fact_check: FactCheckResult


RESUME_GENERATE_JSON_SCHEMA = ResumeGenerateResponse.model_json_schema()
RESUME_JSON_SCHEMA = ResumeJSON.model_json_schema()
FACT_CHECK_JSON_SCHEMA = FactCheckResult.model_json_schema()
