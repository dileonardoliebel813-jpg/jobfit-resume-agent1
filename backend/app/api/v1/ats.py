from fastapi import APIRouter, HTTPException

from app.agents.ats_review_agent import ATSReviewAgent, ATSReviewAgentError
from app.core.llm_client import LLMClientError
from app.schemas.ats_schema import ATSReviewRequest, ATSReviewResponse

router = APIRouter(prefix="/ats", tags=["ats"])


@router.post("/review", response_model=ATSReviewResponse)
def review_ats(payload: ATSReviewRequest) -> ATSReviewResponse:
    try:
        return ATSReviewResponse(ats_review=ATSReviewAgent().review(payload.resume_json))
    except (LLMClientError, ATSReviewAgentError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
