from pydantic import BaseModel, ConfigDict

from app.schemas.resume_schema import ResumeJSON


class ATSIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    severity: str
    message: str
    suggestion: str


class ATSReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int
    keyword_coverage: float
    summary: str
    issues: list[ATSIssue]


class ATSReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resume_json: ResumeJSON


class ATSReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ats_review: ATSReviewResult


ATS_REVIEW_JSON_SCHEMA = ATSReviewResult.model_json_schema()
