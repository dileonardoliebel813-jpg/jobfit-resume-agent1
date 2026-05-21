from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.agents.jd_profiler_agent import JDProfilerAgent, JDProfilerAgentError
from app.core.llm_client import LLMClientError
from app.schemas.jd_schema import JDAnalyzeRequest, JDAnalyzeResponse

router = APIRouter(prefix="/jd", tags=["jd"])


@router.post("/analyze", response_model=JDAnalyzeResponse)
def analyze_jd(payload: JDAnalyzeRequest) -> JDAnalyzeResponse:
    agent = JDProfilerAgent()
    try:
        jd_profile = agent.analyze(payload.raw_jd)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMClientError as exc:
        detail = str(exc)
        if detail == "LLM API call failed":
            detail = (
                "LLM API call failed: 中转站连接中断或响应超时。"
                "请重试一次；如果反复失败，请稍后再试或临时缩短 JD 文本。"
            )
        raise HTTPException(status_code=500, detail=detail) from exc
    except (JDProfilerAgentError, ValidationError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return JDAnalyzeResponse(jd_profile=jd_profile)
