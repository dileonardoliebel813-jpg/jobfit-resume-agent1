from fastapi import APIRouter, HTTPException

from app.agents.resume_parser_agent import ResumeParserAgent, ResumeParserAgentError
from app.core.llm_client import LLMClientError
from app.schemas.profile_schema import ProfileParseRequest, ProfileParseResponse

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("/parse", response_model=ProfileParseResponse)
def parse_profile(payload: ProfileParseRequest) -> ProfileParseResponse:
    agent = ResumeParserAgent()
    try:
        user_profile = agent.parse(payload.profile_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (LLMClientError, ResumeParserAgentError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ProfileParseResponse(user_profile=user_profile)
