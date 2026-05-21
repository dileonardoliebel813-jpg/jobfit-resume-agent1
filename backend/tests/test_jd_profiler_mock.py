from app.agents.jd_profiler_agent import JDProfilerAgent
from app.core.config import settings
from app.schemas.jd_schema import JDProfile


def test_jd_profiler_returns_mock_profile(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODE", "mock")
    settings.LLM_MODE = "mock"

    profile = JDProfilerAgent().analyze(
        "高级产品数据分析师\n负责产品指标分析、SQL 数据提取和实验复盘。"
    )

    assert isinstance(profile, JDProfile)
    assert profile.position
    assert profile.required_skills
    assert profile.resume_strategy.must_highlight
