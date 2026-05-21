from fastapi.testclient import TestClient

from app.agents.resume_writer_agent import ResumeWriterAgent
from app.core.config import settings
from app.core.llm_client import LLMClientError
from app.schemas.evidence_schema import EvidenceItem
from app.schemas.jd_schema import JDProfile, ResumeStrategy
from app.schemas.profile_schema import UserProfile, WorkExperience


def _mock_inputs(client: TestClient) -> tuple[dict, dict]:
    jd_response = client.post(
        "/api/v1/jd/analyze",
        json={
            "raw_jd": (
                "Senior Product Data Analyst\n"
                "Own product metrics, SQL analysis, dashboarding, and experiment readouts."
            )
        },
    )
    profile_response = client.post(
        "/api/v1/profile/parse",
        json={
            "profile_text": (
                "Product analyst with SQL, Python, dashboarding, A/B testing, "
                "and stakeholder communication experience."
            )
        },
    )

    return (
        jd_response.json()["jd_profile"],
        profile_response.json()["user_profile"],
    )


def test_resume_generate_mock_pipeline_runs(client: TestClient) -> None:
    jd_profile, user_profile = _mock_inputs(client)

    response = client.post(
        "/api/v1/resume/generate",
        json={"jd_profile": jd_profile, "user_profile": user_profile},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["resume_json"]["candidate_name"] == "Alex Chen"
    assert body["resume_json"]["target_title"]
    assert body["match"]["overall_score"] > 0
    assert body["evidence"]
    assert "coverage_score" in body
    assert "missing_fields" in body
    assert "generation_recommendation" in body


def test_resume_generate_keeps_skeleton_when_experience_missing(client: TestClient) -> None:
    jd_profile, _ = _mock_inputs(client)

    response = client.post(
        "/api/v1/resume/generate",
        json={
            "jd_profile": jd_profile,
            "user_profile": {
                "name": "候选人",
                "headline": "",
                "skills": [],
                "experiences": [],
                "education": ["自动化本科"],
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    resume = body["resume_json"]
    assert resume["summary"]
    assert resume["projects"]
    assert resume["practice_experiences"]
    assert resume["self_evaluation"]
    assert body["coverage_score"] >= 0
    assert body["generation_recommendation"] in {"ready", "needs_more_info", "not_recommended"}


def test_complete_resume_not_too_short(client: TestClient) -> None:
    jd_profile, user_profile = _mock_inputs(client)

    response = client.post(
        "/api/v1/resume/generate",
        json={"jd_profile": jd_profile, "user_profile": user_profile},
    )

    assert response.status_code == 200
    resume = response.json()["resume_json"]
    assert len(resume["summary"]) >= 3
    assert len(resume["skills"]) >= 10
    assert len(resume["projects"]) >= 1
    assert len(resume["projects"][0]["bullets"]) >= 4
    assert len(resume["self_evaluation"]) >= 3


def test_complete_resume_no_missing_words(client: TestClient) -> None:
    jd_profile, _ = _mock_inputs(client)
    sparse_profile = {
        "name": "韩菁菁",
        "headline": "",
        "skills": ["Python", "React", "FastAPI", "SQLite"],
        "experiences": [],
        "education": ["曲阜师范大学 自动化 本科 2022.9-2026.6"],
    }

    response = client.post(
        "/api/v1/resume/generate",
        json={"jd_profile": jd_profile, "user_profile": sparse_profile},
    )

    assert response.status_code == 200
    resume = response.json()["resume_json"]
    body_text = _resume_body_text(resume)
    for banned_word in ["未提供", "暂无", "缺失", "保守版", "信息不足"]:
        assert banned_word not in body_text


def test_transferable_content_allowed(client: TestClient) -> None:
    jd_profile, user_profile = _mock_inputs(client)

    response = client.post(
        "/api/v1/resume/generate",
        json={"jd_profile": jd_profile, "user_profile": user_profile},
    )

    assert response.status_code == 200
    statuses = _resume_body_statuses(response.json()["resume_json"])
    assert {"transferable", "inferred"} & statuses


def test_side_report_contains_missing_info(client: TestClient) -> None:
    jd_profile, _ = _mock_inputs(client)
    sparse_profile = {
        "name": "韩菁菁",
        "headline": "",
        "skills": [],
        "experiences": [],
        "education": ["曲阜师范大学 自动化 本科 2022.9-2026.6"],
    }

    response = client.post(
        "/api/v1/resume/generate",
        json={"jd_profile": jd_profile, "user_profile": sparse_profile},
    )

    assert response.status_code == 200
    body = response.json()
    resume = body["resume_json"]
    assert resume["side_report"]["missing_info"]
    assert _resume_body_text(resume)
    assert not any(item in _resume_body_text(resume) for item in resume["side_report"]["missing_info"])
    for banned_word in ["未提供", "暂无", "缺失", "保守版", "信息不足"]:
        assert banned_word not in _resume_body_text(resume)
    assert body["coverage_score"] >= 0
    assert body["generation_recommendation"] in {"ready", "needs_more_info", "not_recommended"}


def test_resume_writer_falls_back_when_llm_returns_invalid_json(monkeypatch) -> None:
    class BrokenLLMClient:
        def generate_json(self, *args, **kwargs) -> dict:
            raise LLMClientError("LLM returned invalid JSON")

    monkeypatch.setattr(settings, "LLM_MODE", "real")

    jd_profile = JDProfile(
        position="AI 产品经理",
        job_level="初级",
        job_type="全职",
        hard_requirements=["需求分析", "原型设计"],
        core_tasks=["拆解 AI 产品功能", "协同研发落地"],
        required_skills=["Figma", "SQL", "AI 工具"],
        preferred_experience=["AI 项目实践"],
        hidden_preferences=["理解用户场景"],
        resume_strategy=ResumeStrategy(
            must_highlight=["AI 项目实践"],
            should_weaken=["没有证据的商业化结果"],
            tone="真实、低风险、产品化",
        ),
    )
    user_profile = UserProfile(
        name="候选人",
        headline="AI 产品方向",
        skills=["Figma", "SQL", "Python"],
        experiences=[
            WorkExperience(
                company="",
                role="AI 学习计划助手项目",
                duration="",
                highlights=[
                    "梳理学生学习计划场景",
                    "使用 Figma 设计原型",
                    "使用 SQL 整理基础数据",
                ],
                skills=["Figma", "SQL"],
            )
        ],
        education=["某高校 本科"],
    )

    resume = ResumeWriterAgent(llm_client=BrokenLLMClient()).write(
        jd_profile=jd_profile,
        user_profile=user_profile,
        evidence=[
            EvidenceItem(
                requirement="原型设计",
                matched_experience="AI 学习计划助手项目",
                evidence_snippet="使用 Figma 设计原型",
                confidence=0.8,
            )
        ],
        strategy_notes=[],
    )

    assert resume.candidate_name == "候选人"
    assert resume.projects
    assert len(resume.projects[0].bullets) >= 4
    assert "LLM returned invalid JSON" not in _resume_body_text(resume.model_dump())


def test_resume_reviews_accept_generated_resume(client: TestClient) -> None:
    jd_profile, user_profile = _mock_inputs(client)
    generated = client.post(
        "/api/v1/resume/generate",
        json={"jd_profile": jd_profile, "user_profile": user_profile},
    ).json()["resume_json"]

    ats_response = client.post(
        "/api/v1/resume/ats-review",
        json={"resume_json": generated},
    )
    fact_response = client.post(
        "/api/v1/resume/fact-check",
        json={"resume_json": generated},
    )

    assert ats_response.status_code == 200
    assert ats_response.json()["ats_review"]["score"] >= 70
    assert fact_response.status_code == 200
    assert fact_response.json()["fact_check"]["items"]


def _resume_body_text(resume: dict) -> str:
    pieces: list[str] = [
        resume.get("candidate_name", ""),
        resume.get("target_title", ""),
        resume.get("headline", ""),
        *resume.get("skills", []),
        *resume.get("education", []),
    ]
    pieces.extend(item["text"] for item in resume.get("summary", []))
    pieces.extend(item["text"] for item in resume.get("self_evaluation", []))
    for section in ["projects", "practice_experiences", "campus_or_competition"]:
        for module in resume.get(section, []):
            pieces.append(module.get("title", ""))
            pieces.append(module.get("subtitle", ""))
            pieces.extend(item["text"] for item in module.get("bullets", []))
    return "\n".join(pieces)


def _resume_body_statuses(resume: dict) -> set[str]:
    statuses: set[str] = set()
    statuses.update(item["evidence_status"] for item in resume.get("summary", []))
    statuses.update(item["evidence_status"] for item in resume.get("self_evaluation", []))
    for section in ["projects", "practice_experiences", "campus_or_competition"]:
        for module in resume.get(section, []):
            statuses.update(item["evidence_status"] for item in module.get("bullets", []))
    return statuses
