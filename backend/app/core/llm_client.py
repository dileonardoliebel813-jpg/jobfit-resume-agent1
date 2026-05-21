import json
import time
from collections.abc import Callable
from typing import Any, TypeVar

from app.core.config import settings

T = TypeVar("T")


class LLMClientError(RuntimeError):
    """Raised when the configured LLM provider cannot return a valid result."""


class LLMClient:
    """Unified model boundary for all agents.

    Only JD profiling uses the real provider in phase two. Other agents can
    keep their mock behavior while still sharing this integration point later.
    """

    def __init__(self) -> None:
        self._client: Any | None = None

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> str:
        if settings.LLM_MODE == "mock":
            return "Mock LLM text response."

        if settings.OPENAI_WIRE_API == "chat_completions":
            response = self._call_with_retries(
                lambda: self._openai_client().chat.completions.create(
                    model=model or settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                    temperature=settings.LLM_TEMPERATURE,
                )
            )
            output_text = response.choices[0].message.content
            if not output_text:
                raise LLMClientError("LLM returned empty text")
            return output_text

        response = self._call_with_retries(
            lambda: self._openai_client().responses.create(
                model=model or settings.OPENAI_MODEL,
                reasoning={
                    "effort": reasoning_effort or settings.MODEL_REASONING_EFFORT
                },
                store=not settings.DISABLE_RESPONSE_STORAGE,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        )

        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise LLMClientError("LLM returned empty text")

        return output_text

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        schema_name: str,
        model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> dict[str, Any]:
        if settings.LLM_MODE == "mock":
            return self._mock_json(schema_name, json_schema)

        if settings.OPENAI_WIRE_API == "chat_completions":
            response = self._call_with_retries(
                lambda: self._openai_client().chat.completions.create(
                    model=model or settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": self._build_json_user_prompt(
                                user_prompt,
                                json_schema,
                                schema_name,
                            ),
                        },
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                    temperature=settings.LLM_TEMPERATURE,
                )
            )
            output_text = response.choices[0].message.content
            if not output_text:
                raise LLMClientError("LLM returned empty JSON output")
            return self._parse_json_output(output_text)

        response = self._call_with_retries(
            lambda: self._openai_client().responses.create(
                model=model or settings.OPENAI_MODEL,
                reasoning={
                    "effort": reasoning_effort or settings.MODEL_REASONING_EFFORT
                },
                store=not settings.DISABLE_RESPONSE_STORAGE,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "schema": json_schema,
                        "strict": True,
                    }
                },
            )
        )

        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise LLMClientError("LLM returned empty JSON output")

        return self._parse_json_output(output_text)

    def complete_json(self, prompt: str, schema_name: str) -> dict[str, Any]:
        """Legacy no-op kept for phase-one mock agents.

        This method intentionally never calls the provider so non-JD agents
        remain mock-only in phase two.
        """

        return {
            "schema_name": schema_name,
            "prompt_preview": prompt[:120],
            "mock": True,
        }

    def _parse_json_output(self, output_text: str) -> dict[str, Any]:
        try:
            result = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise LLMClientError("LLM returned invalid JSON") from exc

        if not isinstance(result, dict):
            raise LLMClientError("LLM returned invalid JSON")

        return result

    def _openai_client(self) -> Any:
        if settings.OPENAI_WIRE_API not in {"responses", "chat_completions"}:
            raise LLMClientError("Unsupported OpenAI-compatible wire API")

        if not settings.OPENAI_API_KEY:
            raise LLMClientError("OPENAI_API_KEY is missing when LLM_MODE=real")

        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise LLMClientError(
                    "openai package is required when LLM_MODE=real"
                ) from exc

            kwargs: dict[str, Any] = {
                "api_key": settings.OPENAI_API_KEY,
                "timeout": settings.LLM_TIMEOUT_SECONDS,
                "max_retries": 0,
            }
            if settings.OPENAI_BASE_URL:
                kwargs["base_url"] = settings.OPENAI_BASE_URL

            self._client = OpenAI(**kwargs)

        return self._client

    def _build_json_user_prompt(
        self,
        user_prompt: str,
        json_schema: dict[str, Any],
        schema_name: str,
    ) -> str:
        return (
            f"{user_prompt}\n\n"
            "请只输出一个合法 JSON object，不要输出 Markdown、代码块或解释文字。\n"
            f"JSON object 必须匹配 schema_name={schema_name} 的字段结构。\n"
            "上方用户输入就是唯一可信来源；能从原文直接看出的岗位、技能、职责、项目或经历必须提取。\n"
            "只有某个字段在原文中确实不存在时，才使用“未提供”或空数组。\n"
            "不要因为字段不完整就把整份输入判定为缺失；不要编造原文不存在的信息。\n"
            "JSON Schema:\n"
            f"{json.dumps(json_schema, ensure_ascii=False)}"
        )

    def _call_with_retries(self, call: Callable[[], T]) -> T:
        last_error: Exception | None = None
        max_retries = max(settings.LLM_MAX_RETRIES, 0)

        for attempt in range(max_retries + 1):
            try:
                return call()
            except LLMClientError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt < max_retries:
                    time.sleep(min(0.5 * (attempt + 1), 2.0))

        raise LLMClientError("LLM API call failed") from last_error

    def _mock_json(
        self,
        schema_name: str,
        json_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if schema_name == "jd_profile":
            return {
                "position": "高级产品数据分析师",
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

        if json_schema:
            mock_value = self._mock_value_from_schema(json_schema, json_schema)
            if isinstance(mock_value, dict):
                return mock_value

        return {"mock": True, "schema_name": schema_name}

    def _mock_value_from_schema(
        self,
        schema: dict[str, Any],
        root_schema: dict[str, Any],
    ) -> Any:
        ref = schema.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            definition_name = ref.removeprefix("#/$defs/")
            return self._mock_value_from_schema(
                root_schema.get("$defs", {}).get(definition_name, {}),
                root_schema,
            )

        if "anyOf" in schema:
            candidates = [
                item for item in schema["anyOf"] if item.get("type") != "null"
            ]
            return self._mock_value_from_schema(candidates[0], root_schema)

        schema_type = schema.get("type")
        if schema_type == "object":
            return {
                name: self._mock_value_from_schema(property_schema, root_schema)
                for name, property_schema in schema.get("properties", {}).items()
            }
        if schema_type == "array":
            return [self._mock_value_from_schema(schema.get("items", {}), root_schema)]
        if schema_type == "string":
            return "mock"
        if schema_type == "integer":
            return 1
        if schema_type == "number":
            return 1.0
        if schema_type == "boolean":
            return False

        return None
