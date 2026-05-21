from app.agents.evidence_builder_agent import EvidenceBuilderAgent
from app.agents.evidence_guidance_agent import EvidenceGuidanceAgent
from app.agents.hybrid_match_agent import HybridMatchAgent
from app.agents.resume_writer_agent import ResumeWriterAgent, ResumeWriterAgentError
from app.agents.strategy_agent import StrategyAgent
from app.core.config import settings
from app.core.llm_client import LLMClient
from app.schemas.jd_schema import JDProfile
from app.schemas.profile_schema import UserProfile
from app.schemas.resume_schema import ResumeGenerateResponse


class ResumePipelineError(RuntimeError):
    """Raised when the resume pipeline cannot produce a valid response."""


class ResumePipeline:
    def __init__(
        self,
        evidence_builder: EvidenceBuilderAgent | None = None,
        matcher: HybridMatchAgent | None = None,
        strategist: StrategyAgent | None = None,
        writer: ResumeWriterAgent | None = None,
        evidence_guidance: EvidenceGuidanceAgent | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.evidence_builder = evidence_builder or EvidenceBuilderAgent()
        self.matcher = matcher or HybridMatchAgent()
        self.strategist = strategist or StrategyAgent()
        self.writer = writer or ResumeWriterAgent()
        self.evidence_guidance = evidence_guidance or EvidenceGuidanceAgent()
        self.llm_client = llm_client or LLMClient()

    def generate(
        self,
        jd_profile: JDProfile,
        user_profile: UserProfile,
    ) -> ResumeGenerateResponse:
        evidence = self.evidence_builder.build(jd_profile, user_profile)
        diagnosis = self.evidence_guidance.diagnose(jd_profile, user_profile)

        match = self.matcher.match(jd_profile, user_profile, evidence)
        strategy_notes = self.strategist.plan(jd_profile, user_profile, match)
        try:
            resume_json = self.writer.write(
                jd_profile=jd_profile,
                user_profile=user_profile,
                evidence=evidence,
                strategy_notes=strategy_notes,
                diagnosis=diagnosis,
            )
        except ResumeWriterAgentError as exc:
            raise ResumePipelineError(str(exc)) from exc

        return ResumeGenerateResponse(
            resume_json=resume_json,
            match=match,
            evidence=evidence,
            strategy_notes=strategy_notes,
            coverage_score=diagnosis.coverage_score,
            missing_fields=list(
                dict.fromkeys(
                    item.requirement
                    for item in diagnosis.evidence_items
                    if item.status != "direct_evidence"
                )
            )[:12],
            generation_recommendation=diagnosis.generation_recommendation,
        )
