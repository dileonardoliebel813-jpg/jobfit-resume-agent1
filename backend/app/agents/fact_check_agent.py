from __future__ import annotations

from pydantic import ValidationError

from app.core.config import settings
from app.core.llm_client import LLMClient
from app.core.prompts import (
    FACT_CHECK_COMPLETE_SYSTEM_PROMPT,
    build_fact_check_complete_user_prompt,
)
from app.schemas.profile_schema import UserProfile
from app.schemas.resume_schema import (
    FACT_CHECK_JSON_SCHEMA,
    FactCheckItem,
    FactCheckResult,
    ResumeJSON,
)


class FactCheckAgentError(RuntimeError):
    """Raised when fact checking cannot produce a valid result."""


class FactCheckAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def check(
        self,
        resume_json: ResumeJSON,
        user_profile: UserProfile | None = None,
    ) -> FactCheckResult:
        if settings.LLM_MODE == "real":
            if user_profile is None:
                raise ValueError("user_profile is required for real fact check")

            result = self.llm_client.generate_json(
                system_prompt=FACT_CHECK_COMPLETE_SYSTEM_PROMPT,
                user_prompt=build_fact_check_complete_user_prompt(
                    resume_json.model_dump_json(ensure_ascii=False),
                    user_profile.model_dump_json(ensure_ascii=False),
                ),
                json_schema=FACT_CHECK_JSON_SCHEMA,
                schema_name="fact_check",
                model=settings.OPENAI_REVIEW_MODEL,
                reasoning_effort=settings.REVIEW_REASONING_EFFORT,
            )
            try:
                return FactCheckResult.model_validate(result)
            except ValidationError as exc:
                raise FactCheckAgentError(
                    "LLM returned JSON that does not match FactCheckResult schema"
                ) from exc

        items = self._collect_fact_items(resume_json)
        risk_level = self._risk_level(items)
        summary = self._summary_text(items)

        return FactCheckResult(
            risk_level=risk_level,
            summary=summary,
            items=items[:12],
        )

    def _collect_fact_items(self, resume_json: ResumeJSON) -> list[FactCheckItem]:
        items: list[FactCheckItem] = []

        for section_name, bullets in [
            ("summary", resume_json.summary),
            ("projects", [bullet for module in resume_json.projects for bullet in module.bullets]),
            (
                "practice_experiences",
                [bullet for module in resume_json.practice_experiences for bullet in module.bullets],
            ),
            (
                "campus_or_competition",
                [bullet for module in resume_json.campus_or_competition for bullet in module.bullets],
            ),
            ("self_evaluation", resume_json.self_evaluation),
        ]:
            for bullet in bullets:
                items.append(
                    FactCheckItem(
                        claim=bullet.text,
                        status=bullet.evidence_status,
                        source_hint=section_name,
                        note=self._note_for_status(bullet.evidence_status, section_name),
                    )
                )

        for item in resume_json.education:
            items.append(
                FactCheckItem(
                    claim=item,
                    status="supported",
                    source_hint="education",
                    note="教育背景来自候选人输入，可直接保留。",
                )
            )

        return items

    def _note_for_status(self, status: str, section_name: str) -> str:
        if status == "supported":
            return f"{section_name} 中的内容可直接保留。"
        if status == "transferable":
            return f"{section_name} 中的表达属于能力迁移，建议保持低风险措辞。"
        if status == "inferred":
            return f"{section_name} 中的表达需要用户进一步确认。"
        if status == "unsupported":
            return f"{section_name} 中的这条内容不建议进入正文，应转入 side_report。"
        return f"{section_name} 中的这条内容尚未形成可直接写入的证据。"

    def _risk_level(self, items: list[FactCheckItem]) -> str:
        statuses = {item.status for item in items}
        if statuses & {"unsupported", "missing"}:
            return "high"
        if statuses & {"inferred"}:
            return "medium"
        return "low"

    def _summary_text(self, items: list[FactCheckItem]) -> str:
        transferable = sum(1 for item in items if item.status == "transferable")
        inferred = sum(1 for item in items if item.status == "inferred")
        unsupported = sum(1 for item in items if item.status == "unsupported")
        missing = sum(1 for item in items if item.status == "missing")
        return (
            f"已核对 {len(items)} 条简历要点，"
            f"其中 {transferable} 条为能力迁移，{inferred} 条需要确认，"
            f"{unsupported} 条不建议写入正文，{missing} 条仍待补证。"
        )
