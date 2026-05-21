from fastapi import APIRouter, HTTPException

from app.agents.ats_review_agent import ATSReviewAgent, ATSReviewAgentError
from app.agents.fact_check_agent import FactCheckAgent, FactCheckAgentError
from app.core.llm_client import LLMClientError
from app.schemas.ats_schema import ATSReviewResponse
from app.schemas.resume_schema import (
    FactCheckResponse,
    ResumeGenerateRequest,
    ResumeGenerateResponse,
    ResumeReviewRequest,
)
from app.services.resume_pipeline import ResumePipeline
from app.services.resume_pipeline import ResumePipelineError

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/generate", response_model=ResumeGenerateResponse)
def generate_resume(payload: ResumeGenerateRequest) -> ResumeGenerateResponse:
    try:
        return ResumePipeline().generate(payload.jd_profile, payload.user_profile)
    except (LLMClientError, ResumePipelineError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/ats-review", response_model=ATSReviewResponse)
def review_resume_for_ats(payload: ResumeReviewRequest) -> ATSReviewResponse:
    try:
        review = ATSReviewAgent().review(payload.resume_json, payload.jd_profile)
        return ATSReviewResponse(ats_review=review)
    except (LLMClientError, ATSReviewAgentError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/fact-check", response_model=FactCheckResponse)
def fact_check_resume(payload: ResumeReviewRequest) -> FactCheckResponse:
    try:
        result = FactCheckAgent().check(payload.resume_json, payload.user_profile)
        return FactCheckResponse(fact_check=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (LLMClientError, FactCheckAgentError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
