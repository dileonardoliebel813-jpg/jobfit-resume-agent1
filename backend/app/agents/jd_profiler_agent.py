from pydantic import ValidationError

from app.core.config import settings
from app.core.llm_client import LLMClient
from app.core.prompts import (
    JD_PROFILER_SYSTEM_PROMPT,
    build_jd_profiler_user_prompt,
)
from app.schemas.jd_schema import JD_PROFILE_JSON_SCHEMA, JDProfile


class JDProfilerAgentError(RuntimeError):
    """Raised when JD profiling cannot produce a valid JDProfile."""


class JDProfilerAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm = llm_client or LLMClient()

    def analyze(self, raw_jd: str) -> JDProfile:
        if not raw_jd or not raw_jd.strip():
            raise ValueError("raw_jd cannot be empty")

        if settings.LLM_MODE == "mock":
            return JDProfile.model_validate(self._mock_jd_profile(raw_jd))

        result = self.llm.generate_json(
            system_prompt=JD_PROFILER_SYSTEM_PROMPT,
            user_prompt=build_jd_profiler_user_prompt(raw_jd),
            json_schema=JD_PROFILE_JSON_SCHEMA,
            schema_name="jd_profile",
            model=settings.OPENAI_MODEL,
            reasoning_effort=settings.JD_REASONING_EFFORT,
        )

        try:
            return JDProfile.model_validate(result)
        except ValidationError as exc:
            raise JDProfilerAgentError(
                "LLM returned JSON that does not match JDProfile schema"
            ) from exc

    def _mock_jd_profile(self, raw_jd: str) -> dict:
        first_line = raw_jd.strip().splitlines()[0].strip()
        position = first_line[:80] if first_line else "高级产品数据分析师"

        return {
            "position": position,
            "job_level": "中高级",
            "job_type": "全职",
            "hard_requirements": [
                "熟练使用 SQL 进行数据分析",
                "具备 Python 数据处理经验",
                "能够独立完成产品指标分析",
            ],
            "core_tasks": [
                "分析产品漏斗并识别增长机会",
                "支持实验设计和结果解读",
                "向业务团队输出清晰的数据洞察",
            ],
            "required_skills": [
                "SQL",
                "Python",
                "产品分析",
                "实验分析",
                "沟通表达",
            ],
            "preferred_experience": [
                "有 A/B 测试或增长分析经验",
                "有跨职能团队协作经验",
            ],
            "hidden_preferences": [
                "偏好能把分析结论转化为产品动作的候选人",
                "偏好有指标体系建设经验的候选人",
            ],
            "resume_strategy": {
                "must_highlight": [
                    "量化产品分析成果",
                    "突出 SQL、Python 和实验分析能力",
                ],
                "should_weaken": [
                    "弱化与岗位无关的泛运营描述",
                    "减少没有数据支撑的职责罗列",
                ],
                "tone": "结果导向、数据驱动、表达清晰",
            },
        }
