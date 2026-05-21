from pydantic import ValidationError

from app.core.config import settings
from app.core.llm_client import LLMClient
from app.core.prompts import ATS_REVIEW_SYSTEM_PROMPT, build_ats_review_user_prompt
from app.schemas.ats_schema import ATS_REVIEW_JSON_SCHEMA, ATSIssue, ATSReviewResult
from app.schemas.jd_schema import JDProfile
from app.schemas.resume_schema import ResumeJSON


class ATSReviewAgentError(RuntimeError):
    """Raised when ATS review cannot produce a valid result."""


class ATSReviewAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def review(
        self,
        resume_json: ResumeJSON,
        jd_profile: JDProfile | None = None,
    ) -> ATSReviewResult:
        if settings.LLM_MODE == "real":
            result = self.llm_client.generate_json(
                system_prompt=ATS_REVIEW_SYSTEM_PROMPT,
                user_prompt=build_ats_review_user_prompt(
                    jd_profile.model_dump_json(ensure_ascii=False) if jd_profile else "{}",
                    resume_json.model_dump_json(ensure_ascii=False),
                ),
                json_schema=ATS_REVIEW_JSON_SCHEMA,
                schema_name="ats_review",
                model=settings.OPENAI_REVIEW_MODEL,
                reasoning_effort=settings.REVIEW_REASONING_EFFORT,
            )
            try:
                return ATSReviewResult.model_validate(result)
            except ValidationError as exc:
                raise ATSReviewAgentError(
                    "LLM returned JSON that does not match ATSReviewResult schema"
                ) from exc

        has_keywords = len(resume_json.skills) >= 6
        issues = [
            ATSIssue(
                category="keywords",
                severity="low" if has_keywords else "medium",
                message="Keyword coverage is acceptable for the mock JD profile.",
                suggestion="Keep role-critical keywords in both skills and experience bullets.",
            ),
            ATSIssue(
                category="format",
                severity="low",
                message="JSON structure can be exported into an ATS-friendly single-column resume.",
                suggestion="Avoid complex tables when implementing document export.",
            ),
        ]

        return ATSReviewResult(
            score=86 if has_keywords else 74,
            keyword_coverage=0.82 if has_keywords else 0.62,
            summary="Mock ATS review passed with minor keyword and formatting suggestions.",
            issues=issues,
        )
