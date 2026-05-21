from fastapi import APIRouter

from app.agents.evidence_guidance_agent import EvidenceGuidanceAgent
from app.agents.evidence_builder_agent import EvidenceBuilderAgent
from app.agents.hybrid_match_agent import HybridMatchAgent
from app.schemas.match_schema import MatchDiagnoseRequest, MatchDiagnoseResponse, MatchRequest, MatchResponse

router = APIRouter(prefix="/match", tags=["match"])


@router.post("/analyze", response_model=MatchResponse)
def analyze_match(payload: MatchRequest) -> MatchResponse:
    evidence = EvidenceBuilderAgent().build(payload.jd_profile, payload.user_profile)
    match = HybridMatchAgent().match(payload.jd_profile, payload.user_profile, evidence)
    return MatchResponse(match=match)


@router.post("/diagnose", response_model=MatchDiagnoseResponse)
def diagnose_match(payload: MatchDiagnoseRequest) -> MatchDiagnoseResponse:
    return EvidenceGuidanceAgent().diagnose(
        jd_profile=payload.jd_profile,
        user_profile=payload.user_profile,
        raw_profile_text=payload.raw_profile_text,
        user_confirmed_absent_requirements=payload.user_confirmed_absent_requirements,
    )
