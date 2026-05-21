import json

from pydantic import ValidationError

from app.core.config import settings
from app.core.llm_client import LLMClient
from app.core.prompts import (
    PROFILE_PARSER_SYSTEM_PROMPT,
    build_profile_parser_retry_user_prompt,
    build_profile_parser_user_prompt,
)
from app.schemas.profile_schema import USER_PROFILE_JSON_SCHEMA, UserProfile, WorkExperience


class ResumeParserAgentError(RuntimeError):
    """Raised when profile parsing cannot produce a valid UserProfile."""


class ResumeParserAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def parse(self, profile_text: str) -> UserProfile:
        if not profile_text or not profile_text.strip():
            raise ValueError("profile_text cannot be empty")

        if settings.LLM_MODE == "real":
            result = self.llm_client.generate_json(
                system_prompt=PROFILE_PARSER_SYSTEM_PROMPT,
                user_prompt=build_profile_parser_user_prompt(profile_text),
                json_schema=USER_PROFILE_JSON_SCHEMA,
                schema_name="user_profile",
                model=settings.OPENAI_MODEL,
                reasoning_effort=settings.PROFILE_REASONING_EFFORT,
            )
            profile = self._validate_profile(result)
            if not profile.experiences and self._text_looks_like_experience(profile_text):
                retry_result = self.llm_client.generate_json(
                    system_prompt=PROFILE_PARSER_SYSTEM_PROMPT,
                    user_prompt=build_profile_parser_retry_user_prompt(
                        profile_text,
                        json.dumps(result, ensure_ascii=False),
                    ),
                    json_schema=USER_PROFILE_JSON_SCHEMA,
                    schema_name="user_profile",
                    model=settings.OPENAI_MODEL,
                    reasoning_effort=settings.PROFILE_REASONING_EFFORT,
                )
                profile = self._validate_profile(retry_result)

            if not profile.experiences and self._text_looks_like_experience(profile_text):
                raise ResumeParserAgentError(
                    "LLM did not extract any project or work experience from the provided profile text"
                )

            return profile

        self.llm_client.complete_json(profile_text, "UserProfile")

        return UserProfile(
            name="Alex Chen",
            headline="Data-driven product analyst with end-to-end analytics delivery experience.",
            skills=["Python", "SQL", "Tableau", "Experiment Design", "Product Analytics"],
            experiences=[
                WorkExperience(
                    company="Northstar Labs",
                    role="Product Analyst",
                    duration="2022 - Present",
                    highlights=[
                        "Built funnel dashboards that helped product teams prioritize onboarding fixes.",
                        "Designed A/B test readouts and translated results into roadmap decisions.",
                    ],
                    skills=["SQL", "Python", "Product Analytics", "A/B Testing"],
                ),
                WorkExperience(
                    company="BrightApps",
                    role="Business Analyst",
                    duration="2020 - 2022",
                    highlights=[
                        "Automated weekly reporting and reduced manual analysis time.",
                        "Presented performance insights to sales and customer success leaders.",
                    ],
                    skills=["SQL", "Tableau", "Stakeholder Communication"],
                ),
            ],
            education=["B.S. in Information Systems, Mock University"],
        )

    def _validate_profile(self, result: dict) -> UserProfile:
        try:
            return UserProfile.model_validate(result)
        except ValidationError as exc:
            raise ResumeParserAgentError(
                "LLM returned JSON that does not match UserProfile schema"
            ) from exc

    def _text_looks_like_experience(self, profile_text: str) -> bool:
        no_experience_markers = (
            "没有相关经历",
            "暂无相关经历",
            "没有项目经历",
            "暂无项目经历",
            "没有实习经历",
            "暂无实习经历",
        )
        if any(marker in profile_text for marker in no_experience_markers):
            return False

        markers = (
            "项目",
            "系统",
            "原型",
            "平台",
            "产品",
            "负责",
            "完成",
            "实现",
            "开发",
            "设计",
            "分析",
        )
        return any(marker in profile_text for marker in markers)
